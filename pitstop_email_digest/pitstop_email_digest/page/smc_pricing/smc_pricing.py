"""SMC Pricing: the Service Maintenance Packages that apply to a vehicle, with their price.

Each package is priced on an unsaved Service Maintenance Quotation for the selected Customer
(optional), the way the quotation form prices it: template sales items, Item Price, Pricing Rules
and taxes. Without a Customer, the Customer Group filter stands in for the customer's group.

Pricing Rules are conditioned on the package and customer group, so a package is only listed for
the customer groups it has Pricing Rules for, and nothing is shared between packages: pricing one
takes about a second. The page lists the packages first (get_smc_packages, fast) and then prices
each one (get_smc_package_price).
"""

import re

import frappe
from erpnext.accounts.party import get_default_price_list
from erpnext.setup.doctype.customer_group.customer_group import (
    get_customer_group_subtree,
)
from erpnext.stock.doctype.item_applicable_item.item_applicable_item import (
    filter_applicable_item,
)
from frappe import _
from frappe.model.base_document import get_controller
from frappe.utils import cint, cstr, flt, nowdate

# a package's Pricing Rules name it in their condition
PACKAGE_CONDITION_RE = re.compile(
    r"""service_maintenance_package['"]\)\s*==\s*['"]([^'"]+)['"]"""
)


@frappe.whitelist()
def get_smc_packages(
    vehicle, customer=None, customer_group=None, restrict_on_fuel_type=False
):
    """Vehicle details and every package, with whether it applies to the vehicle.

    With restrict_on_fuel_type, only packages that pick an item conditioned on a fuel type (the
    vehicle's, as the template filters by it) are listed, e.g. EV packages for an Electric vehicle.
    """
    restrict_on_fuel_type = cint(restrict_on_fuel_type)
    ctx = get_context(vehicle, customer, customer_group)
    package_customer_groups = get_package_customer_groups()

    packages = []
    for package in frappe.get_all(
        "Service Maintenance Package",
        fields=["name", "validity_duration", "validity_mileage"],
        order_by="name",
    ):
        if not is_package_for_customer_group(
            package_customer_groups.get(package.name), ctx.customer_group
        ):
            continue

        templates = frappe.get_cached_doc(
            "Service Maintenance Package", package.name
        ).service_templates
        template_items = [
            (
                t,
                get_applicable_items(
                    t.service_template, ctx.item_code, ctx.customer, ctx.customer_group
                ),
            )
            for t in templates
        ]
        if restrict_on_fuel_type and not any(
            sti.get("vehicle_fuel_type") for _, items in template_items for sti in items
        ):
            continue

        # a package applies only when every template gets an item, as the quotation validates
        missing = [
            t.service_template_name or t.service_template
            for t, items in template_items
            if not items
        ]
        packages.append(
            {
                "package": package.name,
                "validity_duration": package.validity_duration,
                "validity_mileage": package.validity_mileage,
                "applicable": bool(templates) and not missing,
                "missing_templates": missing,
            }
        )

    vehicle_doc = ctx.vehicle_doc
    return {
        "vehicle": {
            "name": vehicle_doc.name,
            "item_code": vehicle_doc.item_code,
            "item_name": vehicle_doc.item_name,
            "variant_of": frappe.get_cached_value(
                "Item", vehicle_doc.item_code, "variant_of"
            ),
            "chassis_no": vehicle_doc.get("chassis_no"),
            "license_plate": vehicle_doc.get("license_plate"),
            "fuel_type": frappe.get_cached_value(
                "Item", vehicle_doc.item_code, "vehicle_fuel_type"
            ),
            "current_package": vehicle_doc.get("service_maintenance_package"),
            "smc_status": vehicle_doc.get("smc_status"),
        },
        "company": ctx.company,
        "currency": ctx.currency,
        "selling_price_list": ctx.selling_price_list,
        "customer": ctx.customer,
        "customer_name": ctx.customer_name,
        "customer_group": ctx.customer_group,
        "packages": packages,
    }


@frappe.whitelist()
def get_smc_package_price(vehicle, package, customer=None, customer_group=None):
    """Totals, template amounts and item rates of one package for the vehicle."""
    ctx = get_context(vehicle, customer, customer_group)

    values = {
        "doctype": "Service Maintenance Quotation",
        "__islocal": 1,  # taxes are only set on new documents
        "company": ctx.company,
        "transaction_date": nowdate(),
        "valid_from_date": nowdate(),
        "currency": ctx.currency,
        "applies_to_vehicle": vehicle,
        "service_maintenance_package": package,
    }
    if ctx.customer:
        # price list, customer group and taxes then come from the customer, as on the form
        values.update({"quotation_to": "Customer", "party_name": ctx.customer})
    else:
        # pricing rules read the customer group from the document
        values.update(
            {
                "selling_price_list": ctx.selling_price_list,
                "customer_group": ctx.customer_group,
            }
        )

    doc = get_pricing_doc_class(ctx.customer_group)(values)
    doc.set_contract_values(reset=True)

    return get_package_pricing(doc)


def get_context(vehicle, customer, customer_group):
    frappe.has_permission("Service Maintenance Package", "read", throw=True)
    frappe.has_permission("Vehicle", "read", vehicle, throw=True)
    if customer:
        frappe.has_permission("Customer", "read", customer, throw=True)

    vehicle_doc = frappe.get_doc("Vehicle", vehicle)
    if not vehicle_doc.item_code:
        frappe.throw(_("Vehicle {0} has no Variant Item").format(frappe.bold(vehicle)))

    customer_doc = frappe.get_cached_doc("Customer", customer) if customer else None
    # a selected customer's own group wins over the Customer Group filter
    if customer_doc:
        customer_group = customer_doc.customer_group
    company = frappe.defaults.get_user_default("Company") or frappe.db.get_default(
        "company"
    )

    # same fallback as the quotation: Customer, Customer Group, then Selling Settings
    if customer_doc:
        selling_price_list = get_default_price_list("Customer", customer)
    else:
        selling_price_list = (
            customer_group
            and frappe.get_cached_value(
                "Customer Group", customer_group, "default_price_list"
            )
        ) or frappe.db.get_default("selling_price_list")
    if not selling_price_list:
        frappe.throw(_("Please set a default Selling Price List in Selling Settings"))

    return frappe._dict(
        vehicle_doc=vehicle_doc,
        item_code=vehicle_doc.item_code,
        company=company,
        currency=frappe.get_cached_value("Company", company, "default_currency"),
        selling_price_list=selling_price_list,
        customer=customer or None,
        customer_name=customer_doc.customer_name if customer_doc else None,
        customer_group=customer_group or None,
    )


def get_package_customer_groups():
    """{package: customer groups of its selling Pricing Rules}, None standing for any group.

    Pricing Rules name their package in the condition, e.g.
    doc.get('service_maintenance_package') == 'B2C EV Basic Service Contract - 40K/2 Yrs'
    """
    package_customer_groups = {}
    for d in frappe.db.sql(
        """
        select distinct customer_group, `condition`
        from `tabPricing Rule`
        where disable = 0 and selling = 1 and `condition` like %s
        """,
        "%service_maintenance_package%",
        as_dict=1,
    ):
        match = PACKAGE_CONDITION_RE.search(d.condition)
        if match:
            package_customer_groups.setdefault(match.group(1), set()).add(
                d.customer_group or None
            )

    return package_customer_groups


def is_package_for_customer_group(rule_customer_groups, customer_group):
    # no group to price for, or no package Pricing Rules to tell by: keep the package
    if not customer_group or not rule_customer_groups:
        return True

    # a Pricing Rule applies to the customer group when it is the rule's group or under it
    return any(
        not rule_group or customer_group in get_customer_group_subtree(rule_group)
        for rule_group in rule_customer_groups
    )


def get_pricing_doc_class(customer_group):
    """Service Maintenance Quotation that picks template items for the Customer Group filter."""

    class SMCPricingQuotation(get_controller("Service Maintenance Quotation")):
        def set_service_template_items(self):
            # same as ServiceMaintenanceController.set_service_template_items, with our item picker
            self.set_missing_applies_to_details()
            customer = self.party_name if self.quotation_to == "Customer" else None
            self.items = []

            for template in self.service_templates:
                for sti in get_applicable_items(
                    template.service_template,
                    self.applies_to_item,
                    customer,
                    customer_group,
                ):
                    row = self.append(
                        "items",
                        {
                            "service_template": template.service_template,
                            "service_template_name": template.service_template_name,
                            "service_template_detail": template.name,
                            "item_code": sti.applicable_item_code,
                            "qty_per_template": flt(sti.applicable_qty),
                            "uom": sti.applicable_uom,
                        },
                    )
                    row.qty = row.qty_per_template * flt(template.template_qty)
                    if sti.get("use_template_name") and template.service_template_name:
                        row.item_name = template.service_template_name

    return SMCPricingQuotation


def get_applicable_items(service_template, applies_to_item, customer, customer_group):
    """erpnext get_service_template_items, taking the customer group from the filter."""
    template_doc = frappe.get_cached_doc("Service Template", service_template)

    items = []
    selection_groups_selected = set()
    for pt_item in template_doc.get("sales_items"):
        selection_group = cstr(pt_item.get("selection_group")).upper()
        if selection_group and selection_group in selection_groups_selected:
            continue

        if filter_applicable_item(pt_item, []):
            continue

        # the template checks customer group against the Customer; check it against the
        # filter instead
        other_conditions = frappe._dict(
            pt_item.as_dict(), applies_to_customer_group=None
        )
        if template_doc.filter_applicable_item(
            other_conditions, applies_to_item, customer
        ):
            continue
        if pt_item.get("applies_to_customer_group") and (
            customer_group
            not in get_customer_group_subtree(pt_item.applies_to_customer_group)
        ):
            continue

        items.append(pt_item)
        if selection_group:
            selection_groups_selected.add(selection_group)

    return items


def get_package_pricing(doc):
    return {
        "package": doc.service_maintenance_package,
        "net_total": flt(doc.net_total),
        "total_taxes_and_charges": flt(doc.total_taxes_and_charges),
        "grand_total": flt(doc.grand_total),
        "rounded_total": flt(doc.rounded_total) or flt(doc.grand_total),
        "selling_price_list": doc.selling_price_list,
        "taxes_and_charges": doc.taxes_and_charges,
        "templates": [
            {
                "service_template": t.service_template,
                "service_template_name": t.service_template_name,
                "template_qty": t.template_qty,
                "rate": flt(t.rate),
                "amount": flt(t.amount),
            }
            for t in doc.service_templates
        ],
        "items": [
            {
                "service_template": d.service_template,
                "item_code": d.item_code,
                "item_name": d.item_name,
                "qty": flt(d.qty),
                "uom": d.uom,
                "price_list_rate": flt(d.price_list_rate),
                "rate": flt(d.rate),
                "amount": flt(d.amount),
            }
            for d in doc.items
        ],
    }
