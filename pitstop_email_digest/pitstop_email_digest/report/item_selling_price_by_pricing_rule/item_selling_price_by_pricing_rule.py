# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate

from pitstop_email_digest.utils.pricing import (
    get_last_purchase_rates,
    get_valuation_rates,
    get_warehouses,
)

# Rules that price off cost rather than off a price list.
COST_BASED_RATES = (
    "Valuation Rate",
    "Last Purchase Rate",
    "Higher of Valuation / Last Purchase Rate",
)

# Pricing Rules on an Item Group reach well over a million (item, rule) pairs on a
# large catalogue, so an unfiltered run is paged by item rather than sorted whole.
MAX_ITEMS = 1000


def execute(filters=None):
    return ItemSellingPriceByPricingRule(filters).run()


class ItemSellingPriceByPricingRule:
    """Selling price each Pricing Rule lands on, per item it covers."""

    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.posting_date = getdate(self.filters.posting_date or nowdate())
        self.warehouses = get_warehouses(self.filters.warehouse)
        self.truncated = False

    def run(self):
        rows = self.get_rows()
        if not rows:
            return self.get_columns(), [], self.get_message()

        self.set_cost_rates(rows)
        self.set_base_prices(rows)

        for row in rows:
            self.set_selling_price(row)

        return self.get_columns(), rows, self.get_message()

    # ------------------------------------------------------------------- rows
    def get_rows(self):
        """Every (item, selling rule) pair, however the rule reaches the item."""
        self.get_rule_scope()
        if not (self.by_item_code or self.by_item_group or self.by_brand):
            return []

        rows = []
        for item in self.get_items():
            for rule, matched_via in self.rules_for(item):
                rows.append(
                    frappe._dict(
                        item_code=item.item_code,
                        item_name=item.item_name,
                        item_valuation_rate=item.valuation_rate,
                        item_last_purchase_rate=flt(item.last_purchase_rate),
                        matched_via=matched_via,
                        **rule,
                    )
                )

        return rows

    def get_rule_scope(self):
        """Valid selling rules, indexed by what they key on."""
        rules = frappe.db.sql(
            """
            select
                pr.name as pricing_rule, pr.title as pricing_rule_title,
                pr.margin_type, pr.margin_rate_or_amount,
                pr.rate_or_discount, pr.rate, pr.discount_percentage, pr.discount_amount,
                pr.currency, pr.from_price_list, pr.for_price_list
            from `tabPricing Rule` pr
            where pr.disable = 0 and pr.selling = 1
                and ifnull(pr.valid_from, '0001-01-01') <= %(posting_date)s
                and ifnull(pr.valid_upto, '9999-12-31') >= %(posting_date)s
        """,
            {"posting_date": self.posting_date},
            as_dict=1,
        )

        self.by_item_code = {}
        self.by_item_group = {}
        self.by_brand = {}

        if not rules:
            return

        by_name = {d.pricing_rule: d for d in rules}
        names = list(by_name.keys())

        def index(rows, target, key):
            for d in rows:
                rule = by_name.get(d.parent)
                if rule:
                    target.setdefault(d.get(key), []).append(rule)

        index(
            frappe.db.sql(
                """
            select parent, item_code from `tabPricing Rule Item Code`
            where parenttype = 'Pricing Rule' and parent in %(names)s
        """,
                {"names": names},
                as_dict=1,
            ),
            self.by_item_code,
            "item_code",
        )

        # a rule on a parent group also covers every group beneath it
        index(
            frappe.db.sql(
                """
            select prig.parent, child.name as item_group
            from `tabPricing Rule Item Group` prig
            inner join `tabItem Group` rule_group on rule_group.name = prig.item_group
            inner join `tabItem Group` child
                on child.lft >= rule_group.lft and child.rgt <= rule_group.rgt
            where prig.parenttype = 'Pricing Rule' and prig.parent in %(names)s
        """,
                {"names": names},
                as_dict=1,
            ),
            self.by_item_group,
            "item_group",
        )

        index(
            frappe.db.sql(
                """
            select parent, brand from `tabPricing Rule Brand`
            where parenttype = 'Pricing Rule' and parent in %(names)s
        """,
                {"names": names},
                as_dict=1,
            ),
            self.by_brand,
            "brand",
        )

    def get_items(self):
        """Items any valid rule reaches, walked in name order so a capped run is
        stable rather than an arbitrary slice."""
        conditions = []
        values = {}

        if self.by_item_code:
            conditions.append("i.name in %(item_codes)s")
            values["item_codes"] = list(self.by_item_code.keys())
        if self.by_item_group:
            conditions.append("i.item_group in %(item_groups)s")
            values["item_groups"] = list(self.by_item_group.keys())
        if self.by_brand:
            conditions.append("i.brand in %(brands)s")
            values["brands"] = list(self.by_brand.keys())

        where = "({0})".format(" or ".join(conditions))

        limit = MAX_ITEMS + 1
        if self.filters.item_code:
            where += " and i.name = %(item_code)s"
            values["item_code"] = self.filters.item_code
            limit = 1

        items = frappe.db.sql(
            f"""
            select
                i.name as item_code, i.item_name, i.item_group, i.brand,
                i.valuation_rate, i.last_purchase_rate
            from `tabItem` i
            where {where}
            order by i.name
            limit {limit}
        """,
            values,
            as_dict=1,
        )

        if len(items) > MAX_ITEMS:
            self.truncated = True
            items = items[:MAX_ITEMS]

        self.item_count = len(items)
        return items

    def rules_for(self, item):
        """(rule, how it matched) for one item, a rule counted once."""
        seen = set()
        matched = []

        for rules, label in (
            (self.by_item_code.get(item.item_code), _("Item Code")),
            (self.by_item_group.get(item.item_group), _("Item Group")),
            (self.by_brand.get(item.brand), _("Brand")),
        ):
            for rule in rules or []:
                if rule.pricing_rule in seen:
                    continue
                seen.add(rule.pricing_rule)
                matched.append((rule, label))

        matched.sort(key=lambda pair: pair[0].pricing_rule)
        return matched

    # ------------------------------------------------------------------ rates
    def set_cost_rates(self, rows):
        """Valuation and last purchase rate, for the warehouses in scope.

        Both differ by warehouse, so with no Warehouse filter these are figures
        across every warehouse -- a weighted average valuation, and the latest
        purchase anywhere. Pick a warehouse to get what a transaction there would
        actually use.
        """
        item_codes = list({d.item_code for d in rows})

        valuation = get_valuation_rates(item_codes, self.warehouses)
        last_purchase = get_last_purchase_rates(
            item_codes, self.warehouses, self.posting_date
        )

        for row in rows:
            row.valuation_rate = valuation.get(row.item_code) or flt(
                row.item_valuation_rate
            )

            rate = last_purchase.get(row.item_code)
            if rate is not None:
                row.last_purchase_rate = flt(rate)
            elif self.warehouses:
                # erpnext does not fall back to the global rate once a warehouse is
                # in play, and neither does the rule being reported on
                row.last_purchase_rate = 0.0
            else:
                row.last_purchase_rate = flt(row.item_last_purchase_rate)

    def set_base_prices(self, rows):
        """Item Price only matters to the discount and price-list rules, so only
        those items are looked up rather than every item on the report."""
        self.base_prices = {}

        wanted = {}
        for row in rows:
            price_list = self.price_list_for(row)
            if price_list:
                wanted.setdefault(price_list, set()).add(row.item_code)

        if not wanted:
            return

        for price_list, item_codes in wanted.items():
            prices = frappe.db.sql(
                """
                select item_code, price_list_rate, currency
                from `tabItem Price`
                where price_list = %(price_list)s
                    and item_code in %(item_codes)s
                    and ifnull(valid_from, '0001-01-01') <= %(posting_date)s
                    and ifnull(valid_upto, '9999-12-31') >= %(posting_date)s
                order by valid_from desc, modified desc
            """,
                {
                    "price_list": price_list,
                    "item_codes": list(item_codes),
                    "posting_date": self.posting_date,
                },
                as_dict=1,
            )

            for d in prices:
                # ordered newest first, so the first row per item wins
                self.base_prices.setdefault((price_list, d.item_code), d)

    def price_list_for(self, row):
        """Which price list this rule starts from, if it starts from one at all."""
        if row.rate_or_discount == "Price List Rate":
            return row.from_price_list
        if row.rate_or_discount in ("Discount Percentage", "Discount Amount"):
            return row.for_price_list or self.default_selling_price_list()
        return None

    def default_selling_price_list(self):
        if not hasattr(self, "_default_price_list"):
            self._default_price_list = frappe.db.get_single_value(
                "Selling Settings", "selling_price_list"
            )
        return self._default_price_list

    # ---------------------------------------------------------- selling price
    def set_selling_price(self, row):
        """Mirrors how the Pricing Rule itself resolves a rate."""
        rate_or_discount = row.rate_or_discount

        if rate_or_discount == "Rate":
            row.selling_price = flt(row.rate)
            row.based_on = _("Fixed rate set by the rule")
            return

        if rate_or_discount in COST_BASED_RATES:
            self.set_cost_based_price(row, rate_or_discount)
            return

        price_list = self.price_list_for(row)
        base = self.base_prices.get((price_list, row.item_code)) if price_list else None

        if not base:
            row.selling_price = 0
            row.based_on = _("No Item Price in {0}").format(
                price_list or _("any price list")
            )
            return

        rate = self.apply_margin(row, flt(base.price_list_rate))

        if rate_or_discount == "Price List Rate":
            row.selling_price = rate
            row.based_on = _("Rate from {0}").format(price_list)
        elif rate_or_discount == "Discount Percentage":
            row.selling_price = rate - rate * flt(row.discount_percentage) / 100
            row.based_on = _("{0}% off {1}").format(
                flt(row.discount_percentage), price_list
            )
        else:
            row.selling_price = rate - flt(row.discount_amount)
            row.based_on = _("{0} off {1}").format(flt(row.discount_amount), price_list)

    def set_cost_based_price(self, row, rate_or_discount):
        valuation_rate = flt(row.valuation_rate)
        last_purchase_rate = flt(row.last_purchase_rate)

        if rate_or_discount == "Valuation Rate":
            rate = valuation_rate
            based_on = _("Valuation Rate")
        elif rate_or_discount == "Last Purchase Rate":
            # erpnext falls back to valuation when there is no last purchase rate
            rate = last_purchase_rate or valuation_rate
            based_on = (
                _("Last Purchase Rate")
                if last_purchase_rate
                else _("Valuation Rate (no last purchase rate)")
            )
        else:
            rate = max(last_purchase_rate, valuation_rate)
            based_on = _("Higher of Valuation / Last Purchase Rate")

        if not rate:
            row.selling_price = 0
            row.based_on = _("No valuation or last purchase rate")
            return

        row.selling_price = self.apply_margin(row, rate)
        row.based_on = based_on

    def apply_margin(self, row, rate):
        margin = flt(row.margin_rate_or_amount)
        if not margin:
            return flt(rate)
        if row.margin_type == "Percentage":
            return flt(rate) + flt(rate) * margin / 100
        if row.margin_type == "Amount":
            return flt(rate) + margin
        return flt(rate)

    # --------------------------------------------------------------- display
    def get_message(self):
        notes = []

        if not self.filters.warehouse:
            notes.append(
                _(
                    "Valuation Rate and Last Purchase Rate differ by warehouse. With no Warehouse "
                    "filter these are across all warehouses, so a cost-based rule's Selling Price "
                    "is indicative - pick a Warehouse for the rate a transaction there would use."
                )
            )

        if self.truncated:
            notes.append(
                _(
                    "Showing the first {0} items in name order. Pricing Rules on an Item Group reach "
                    "far more items than that - filter by Item to look one up directly."
                ).format(self.item_count)
            )

        return "<br>".join(notes) if notes else None

    def get_columns(self):
        return [
            {
                "label": _("Item"),
                "fieldname": "item_code",
                "fieldtype": "Link",
                "options": "Item",
                "width": 160,
            },
            {
                "label": _("Item Name"),
                "fieldname": "item_name",
                "fieldtype": "Data",
                "width": 220,
            },
            {
                "label": _("Pricing Rule"),
                "fieldname": "pricing_rule",
                "fieldtype": "Link",
                "options": "Pricing Rule",
                "width": 200,
            },
            {
                "label": _("Matched Via"),
                "fieldname": "matched_via",
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "label": _("Margin Type"),
                "fieldname": "margin_type",
                "fieldtype": "Data",
                "width": 110,
            },
            {
                "label": _("Margin Rate or Amount"),
                "fieldname": "margin_rate_or_amount",
                "fieldtype": "Float",
                "width": 170,
            },
            {
                "label": _("Last Purchase Rate"),
                "fieldname": "last_purchase_rate",
                "fieldtype": "Currency",
                "width": 150,
            },
            {
                "label": _("Valuation Rate"),
                "fieldname": "valuation_rate",
                "fieldtype": "Currency",
                "width": 130,
            },
            {
                "label": _("Selling Price"),
                "fieldname": "selling_price",
                "fieldtype": "Currency",
                "width": 130,
            },
            {
                "label": _("Based On"),
                "fieldname": "based_on",
                "fieldtype": "Data",
                "width": 240,
            },
        ]
