import re

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, nowdate
from frappe.utils.nestedset import get_ancestors_of

RULE_FIELDS = [
    "name",
    "title",
    "disable",
    "apply_on",
    "price_or_product_discount",
    "applicable_for",
    "customer",
    "customer_group",
    "territory",
    "sales_partner",
    "campaign",
    "min_qty",
    "max_qty",
    "min_amt",
    "max_amt",
    "valid_from",
    "valid_upto",
    "company",
    "currency",
    "for_price_list",
    "from_price_list",
    "rate_or_discount",
    "rate",
    "discount_percentage",
    "discount_amount",
    "margin_type",
    "margin_rate_or_amount",
    "include_margin_in_price_list_rate",
    "same_item",
    "free_item",
    "free_qty",
    "priority",
    "apply_multiple_pricing_rules",
    "condition",
    "warehouse",
]

SCOPE_TABLES = {
    "Item Code": ("Pricing Rule Item Code", "item_code"),
    "Item Group": ("Pricing Rule Item Group", "item_group"),
    "Brand": ("Pricing Rule Brand", "brand"),
}

COST_BASED = (
    "Valuation Rate",
    "Last Purchase Rate",
    "Higher of Valuation / Last Purchase Rate",
)
SMC_FIELD = "service_maintenance_package"
SMC_PACKAGE_RE = re.compile(SMC_FIELD + r"""['"]\)\s*==\s*['"](.+?)['"]""")


@frappe.whitelist()
def get_pricing_rules(
    item_code=None, customer=None, customer_group=None, rate_based_on=None, show_smc=0
):
    """Return selling pricing rules relevant to the given item / customer / customer group,
    each with a status, a plain-language reason for why it matched and, when an item is given,
    the item's cost and the selling rate the rule would produce."""
    frappe.has_permission("Pricing Rule", "read", throw=True)

    filters = {"selling": 1}
    if rate_based_on:
        filters["rate_or_discount"] = rate_based_on

    rules = frappe.get_all(
        "Pricing Rule",
        filters=filters,
        fields=RULE_FIELDS,
        order_by="priority desc, modified desc",
    )

    if not cint(show_smc):
        rules = [r for r in rules if not _is_smc_rule(r)]

    item_ctx = _get_item_context(item_code)
    party_ctx = _get_party_context(customer, customer_group)
    context = {**item_ctx, **party_ctx}
    if not rules:
        return {"rules": [], "context": context}

    scope = _get_scope_values([r.name for r in rules])
    rule_customer_groups = (
        _get_rule_customer_groups(rules) if (customer_group and not customer) else {}
    )
    costs = ItemCosts(item_code) if item_code else None

    today = getdate(nowdate())
    result = []
    for rule in rules:
        rule.scope_values = scope.get(rule.apply_on, {}).get(rule.name, [])

        item_reason = _match_item(rule, item_ctx)
        if item_reason is None:
            continue
        party_reason = _match_party(rule, party_ctx, rule_customer_groups)
        if party_reason is None:
            continue

        rule.reasons = [r for r in (item_reason, party_reason) if r]
        rule.status = _get_status(rule, today)
        rule.is_smc = _is_smc_rule(rule)
        smc_package = SMC_PACKAGE_RE.search(rule.condition or "")
        rule.smc_package = smc_package.group(1) if smc_package else None
        if costs and rule.price_or_product_discount == "Price":
            rule.pricing = _get_pricing(rule, costs)
        result.append(rule)

    if costs:
        context["cost"] = costs.valuation(None)
        context["default_price_list"] = costs.default_price_list
        context["list_rate"] = costs.price_list_rate(costs.default_price_list)

    return {"rules": result, "context": context}


def _is_smc_rule(rule):
    return SMC_FIELD in (rule.condition or "")


class ItemCosts:
    """Cached cost / price lookups for one item, keyed by warehouse or price list."""

    def __init__(self, item_code):
        self.item_code = item_code
        self.default_price_list = (
            frappe.db.get_single_value("Selling Settings", "selling_price_list")
            or "Standard Selling"
        )
        self._cache = {}

    def _cached(self, key, fn):
        if key not in self._cache:
            self._cache[key] = fn()
        return self._cache[key]

    def valuation(self, warehouse):
        return self._cached(
            ("valuation", warehouse), lambda: self._get_valuation(warehouse)
        )

    def _get_valuation(self, warehouse):
        if warehouse:
            return flt(
                frappe.db.get_value(
                    "Bin",
                    {"item_code": self.item_code, "warehouse": warehouse},
                    "valuation_rate",
                )
            )
        # No warehouse on the rule: use the weighted average across all warehouses holding stock
        stock_value, qty = frappe.db.sql(
            """select sum(stock_value), sum(actual_qty) from `tabBin`
			where item_code = %s and actual_qty > 0""",
            self.item_code,
        )[0]
        if flt(qty) > 0:
            return flt(stock_value) / flt(qty)
        return flt(frappe.get_cached_value("Item", self.item_code, "valuation_rate"))

    def last_purchase_rate(self, warehouse):
        from erpnext.stock.get_item_details import get_last_purchase_rate

        return self._cached(
            ("lpr", warehouse),
            lambda: flt(
                get_last_purchase_rate(
                    self.item_code,
                    warehouse=warehouse,
                    fallback_global_last_purchase_rate=not warehouse,
                )
            ),
        )

    def price_list_rate(self, price_list):
        def fetch():
            rate = frappe.db.sql(
                """select price_list_rate from `tabItem Price`
				where item_code = %(item_code)s and price_list = %(price_list)s
					and ifnull(customer, '') = ''
					and ifnull(valid_from, '2000-01-01') <= %(today)s
					and ifnull(valid_upto, '2500-12-31') >= %(today)s
				order by valid_from desc limit 1""",
                {
                    "item_code": self.item_code,
                    "price_list": price_list,
                    "today": nowdate(),
                },
            )
            return flt(rate[0][0]) if rate else None

        return self._cached(("price", price_list), fetch)


def _get_pricing(rule, costs):
    """Mirror erpnext's apply_price_discount_rule to estimate the selling rate for this item."""
    basis = rule.rate_or_discount
    cost = costs.valuation(rule.warehouse)
    where = rule.warehouse or _("all warehouses")

    if basis == "Rate":
        base, base_label = flt(rule.rate), _("Fixed rate on rule")
    elif basis == "Price List Rate":
        base = costs.price_list_rate(rule.from_price_list)
        base_label = _("Rate from price list {0}").format(rule.from_price_list)
    elif basis in COST_BASED:
        lpr = (
            costs.last_purchase_rate(rule.warehouse) if basis != "Valuation Rate" else 0
        )
        if basis == "Higher of Valuation / Last Purchase Rate":
            base = max(lpr, cost)
        elif basis == "Last Purchase Rate":
            base = lpr or cost
        else:
            base = cost
        base_label = _("{0} ({1})").format(basis, where)
    else:  # Discount Percentage / Discount Amount work off the price list rate
        price_list = rule.for_price_list or costs.default_price_list
        base = costs.price_list_rate(price_list)
        base_label = _("Rate from price list {0}").format(price_list)

    pricing = frappe._dict(
        cost=cost,
        cost_label=_("Valuation rate ({0})").format(where),
        base_rate=base,
        base_label=base_label,
    )
    if base is None:
        pricing.missing = _(
            "No Item Price found, so the selling rate can't be worked out"
        )
        return pricing

    rate = flt(base)
    if rule.margin_type and flt(rule.margin_rate_or_amount):
        if rule.margin_type == "Percentage":
            pricing.margin = rate * flt(rule.margin_rate_or_amount) / 100
        else:
            pricing.margin = flt(rule.margin_rate_or_amount)
        rate += pricing.margin

    if basis == "Discount Percentage":
        pricing.discount = rate * min(100, flt(rule.discount_percentage)) / 100
    elif basis == "Discount Amount":
        pricing.discount = flt(rule.discount_amount)
    rate -= flt(pricing.discount)

    pricing.selling_rate = rate
    if cost:
        pricing.profit = rate - cost
        pricing.profit_pct = pricing.profit / cost * 100
    return pricing


def _get_scope_values(names):
    scope = {}
    for apply_on, (child_doctype, field) in SCOPE_TABLES.items():
        rows = frappe.get_all(
            child_doctype,
            filters={"parenttype": "Pricing Rule", "parent": ["in", names]},
            fields=["parent", field],
        )
        by_rule = scope.setdefault(apply_on, {})
        for row in rows:
            by_rule.setdefault(row.parent, []).append(row.get(field))
    return scope


def _with_ancestors(doctype, name):
    if not name:
        return []
    return [name, *get_ancestors_of(doctype, name)]


def _get_item_context(item_code):
    if not item_code:
        return {}
    item = frappe.get_cached_value(
        "Item", item_code, ["item_name", "item_group", "brand"], as_dict=True
    )
    if not item:
        frappe.throw(_("Item {0} not found").format(item_code))
    return {
        "item_code": item_code,
        "item_name": item.item_name,
        "item_group": item.item_group,
        "brand": item.brand,
        "item_groups": _with_ancestors("Item Group", item.item_group),
    }


def _get_party_context(customer, customer_group):
    ctx = {}
    if customer:
        cust = frappe.get_cached_value(
            "Customer",
            customer,
            ["customer_name", "customer_group", "territory"],
            as_dict=True,
        )
        if not cust:
            frappe.throw(_("Customer {0} not found").format(customer))
        ctx.update(
            customer=customer,
            customer_name=cust.customer_name,
            territory=cust.territory,
            territories=_with_ancestors("Territory", cust.territory),
        )
        customer_group = customer_group or cust.customer_group

    if customer_group:
        ctx.update(
            customer_group=customer_group,
            customer_groups=_with_ancestors("Customer Group", customer_group),
        )
    return ctx


def _get_rule_customer_groups(rules):
    customers = list(
        {r.customer for r in rules if r.applicable_for == "Customer" and r.customer}
    )
    if not customers:
        return {}
    return dict(
        frappe.get_all(
            "Customer",
            filters={"name": ["in", customers]},
            fields=["name", "customer_group"],
            as_list=True,
        )
    )


def _match_item(rule, ctx):
    """Return a reason string if the rule covers the item, '' if no item filter, None if no match."""
    if not ctx:
        return ""
    if rule.apply_on == "Transaction":
        return _("Applies on the whole transaction (any item)")

    values = rule.scope_values
    if rule.apply_on == "Item Code" and ctx["item_code"] in values:
        return _("Item {0} is listed directly").format(ctx["item_code"])
    if rule.apply_on == "Item Group":
        for group in ctx["item_groups"]:
            if group in values:
                if group == ctx["item_group"]:
                    return _("Item belongs to item group {0}").format(group)
                return _("Item group {0} is under parent group {1}").format(
                    ctx["item_group"], group
                )
    if rule.apply_on == "Brand" and ctx.get("brand") and ctx["brand"] in values:
        return _("Item brand is {0}").format(ctx["brand"])
    return None


def _match_party(rule, ctx, rule_customer_groups):
    """Return a reason string if the rule covers the customer / group, '' if no filter, None if no match."""
    if not ctx:
        return ""
    if not rule.applicable_for:
        return _("Open to all customers")

    if rule.applicable_for == "Customer":
        if ctx.get("customer"):
            return (
                _("Made for this customer")
                if rule.customer == ctx["customer"]
                else None
            )
        group = rule_customer_groups.get(rule.customer)
        if group in ctx.get("customer_groups", []):
            return _("Customer {0} is in group {1}").format(rule.customer, group)
        return None

    if rule.applicable_for == "Customer Group" and rule.customer_group in ctx.get(
        "customer_groups", []
    ):
        if rule.customer_group == ctx["customer_group"]:
            return _("Customer group is {0}").format(rule.customer_group)
        return _("Customer group {0} is under parent group {1}").format(
            ctx["customer_group"], rule.customer_group
        )

    if rule.applicable_for == "Territory" and rule.territory in ctx.get(
        "territories", []
    ):
        return _("Customer territory {0} is covered").format(ctx["territory"])

    return None


def _get_status(rule, today):
    if rule.disable:
        return "Disabled"
    if rule.valid_upto and getdate(rule.valid_upto) < today:
        return "Expired"
    if rule.valid_from and getdate(rule.valid_from) > today:
        return "Upcoming"
    return "Active"
