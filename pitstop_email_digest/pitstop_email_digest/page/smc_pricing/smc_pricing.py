"""SMC Pricing: the Service Maintenance Packages that apply to a vehicle, with their price.

Each package is priced on an unsaved Service Maintenance Quotation for the selected Customer
(optional), the way the quotation form prices it: template sales items, Item Price, Pricing Rules
and taxes. The Fuel Type filter stands in for the vehicle's fuel type.

Pricing Rules are conditioned on the package and template, so nothing is shared between
packages and pricing one takes about a second. The page lists the packages first
(get_smc_packages, fast) and then prices each one (get_smc_package_price).
"""

import frappe
from automotive.automotive.doctype.vehicle_fuel_type.vehicle_fuel_type import (
    get_vehicle_fuel_type_subtree,
)
from erpnext.accounts.doctype.pricing_rule.utils import _get_tree_conditions
from erpnext.accounts.party import get_default_price_list
from erpnext.stock.doctype.item_applicable_item.item_applicable_item import (
    filter_applicable_item,
)
from frappe import _
from frappe.model.base_document import get_controller
from frappe.utils import cstr, flt, nowdate


@frappe.whitelist()
def get_smc_packages(vehicle, customer=None, fuel_type=None):
    """Vehicle details and every package, with whether it applies to the vehicle."""
    ctx = get_context(vehicle, customer, fuel_type)

    packages = []
    for package in frappe.get_all(
        "Service Maintenance Package",
        fields=["name", "validity_duration", "validity_mileage"],
        order_by="name",
    ):
        templates = frappe.get_cached_doc(
            "Service Maintenance Package", package.name
        ).service_templates
        # a package applies only when every template gets an item, as the quotation validates
        missing = [
            t.service_template_name or t.service_template
            for t in templates
            if not get_applicable_items(
                t.service_template, ctx.item_code, ctx.customer, ctx.fuel_type
            )
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
            "fuel_type": ctx.vehicle_fuel_type,
            "current_package": vehicle_doc.get("service_maintenance_package"),
            "smc_status": vehicle_doc.get("smc_status"),
        },
        "company": ctx.company,
        "currency": ctx.currency,
        "selling_price_list": ctx.selling_price_list,
        "customer": ctx.customer,
        "customer_name": ctx.customer_name,
        "customer_group": ctx.customer_group,
        "fuel_type": ctx.fuel_type,
        "packages": packages,
    }


@frappe.whitelist()
def get_smc_package_price(vehicle, package, customer=None, fuel_type=None):
    """Totals, template amounts and item rates of one package for the vehicle."""
    ctx = get_context(vehicle, customer, fuel_type)

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
        values["selling_price_list"] = ctx.selling_price_list

    doc = get_pricing_doc_class(ctx.fuel_type)(values)

    # pricing rules take the fuel type from the vehicle's Item; see set_pricing_rule_fuel_type
    frappe.flags.smc_pricing_fuel_type = (
        ctx.fuel_type if ctx.fuel_type != ctx.vehicle_fuel_type else None
    )
    try:
        doc.set_contract_values(reset=True)
    finally:
        frappe.flags.smc_pricing_fuel_type = None

    return get_package_pricing(doc)


def get_context(vehicle, customer, fuel_type):
    frappe.has_permission("Service Maintenance Package", "read", throw=True)
    frappe.has_permission("Vehicle", "read", vehicle, throw=True)
    if customer:
        frappe.has_permission("Customer", "read", customer, throw=True)

    vehicle_doc = frappe.get_doc("Vehicle", vehicle)
    if not vehicle_doc.item_code:
        frappe.throw(_("Vehicle {0} has no Variant Item").format(frappe.bold(vehicle)))

    customer_doc = frappe.get_cached_doc("Customer", customer) if customer else None
    company = frappe.defaults.get_user_default("Company") or frappe.db.get_default(
        "company"
    )

    # same fallback as the quotation: Customer, Customer Group, then Selling Settings
    selling_price_list = (
        customer_doc and get_default_price_list(customer_doc)
    ) or frappe.db.get_default("selling_price_list")
    if not selling_price_list:
        frappe.throw(_("Please set a default Selling Price List in Selling Settings"))

    # the quotation reads the fuel type from the variant Item only, so do the same
    vehicle_fuel_type = frappe.get_cached_value(
        "Item", vehicle_doc.item_code, "vehicle_fuel_type"
    )

    return frappe._dict(
        vehicle_doc=vehicle_doc,
        item_code=vehicle_doc.item_code,
        company=company,
        currency=frappe.get_cached_value("Company", company, "default_currency"),
        selling_price_list=selling_price_list,
        customer=customer or None,
        customer_name=customer_doc.customer_name if customer_doc else None,
        customer_group=customer_doc.customer_group if customer_doc else None,
        vehicle_fuel_type=vehicle_fuel_type,
        fuel_type=fuel_type or vehicle_fuel_type,
    )


def set_pricing_rule_fuel_type(conditions, values, args):
    """update_pricing_rule_parent_doc_conditions hook, runs after automotive's.

    automotive filters Pricing Rules by the Item's fuel type; while this page prices a package for
    another fuel type, swap that condition for the selected one. Does nothing otherwise.
    """
    fuel_type = frappe.flags.get("smc_pricing_fuel_type")
    if not fuel_type or not args.get("applies_to_item"):
        return

    item_condition = _get_tree_conditions(
        "Vehicle Fuel Type", args.get("vehicle_fuel_type"), "vehicle_fuel_type"
    )
    if item_condition in conditions:
        conditions[conditions.index(item_condition)] = _get_tree_conditions(
            "Vehicle Fuel Type", fuel_type, "vehicle_fuel_type"
        )
        args.vehicle_fuel_type = fuel_type


def get_pricing_doc_class(fuel_type):
    """Service Maintenance Quotation that picks template items for the Fuel Type filter."""

    class SMCPricingQuotation(get_controller("Service Maintenance Quotation")):
        def set_service_template_items(self):
            # same as ServiceMaintenanceController.set_service_template_items, with our item picker
            self.set_missing_applies_to_details()
            customer = self.party_name if self.quotation_to == "Customer" else None
            self.items = []

            for template in self.service_templates:
                for sti in get_applicable_items(
                    template.service_template, self.applies_to_item, customer, fuel_type
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


def get_applicable_items(service_template, applies_to_item, customer, fuel_type):
    """erpnext get_service_template_items, taking the fuel type from the filter."""
    template_doc = frappe.get_cached_doc("Service Template", service_template)

    items = []
    selection_groups_selected = set()
    for pt_item in template_doc.get("sales_items"):
        selection_group = cstr(pt_item.get("selection_group")).upper()
        if selection_group and selection_group in selection_groups_selected:
            continue

        if filter_applicable_item(pt_item, []):
            continue

        # the template checks fuel type against the Item; check it against the filter instead
        other_conditions = frappe._dict(pt_item.as_dict(), vehicle_fuel_type=None)
        if template_doc.filter_applicable_item(
            other_conditions, applies_to_item, customer
        ):
            continue
        if pt_item.get("vehicle_fuel_type") and (
            fuel_type not in get_vehicle_fuel_type_subtree(pt_item.vehicle_fuel_type)
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
