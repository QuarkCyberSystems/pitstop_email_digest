import json

import frappe


@frappe.whitelist()
def get_vehicle(fields=None, filters=None):
    if isinstance(fields, str):
        fields = json.loads(fields)

    if isinstance(filters, str):
        filters = json.loads(filters)

    fields = fields or ["name"]
    filters = filters or {}

    email = filters.pop("email", None)

    vehicle = frappe.qb.DocType("Vehicle")
    customer = frappe.qb.DocType("Customer")

    query = (
        frappe.qb.from_(vehicle)
        .left_join(customer)
        .on(vehicle.customer == customer.name)
    )

    # Select fields
    if fields == ["*"]:
        query = query.select(vehicle.star)
    else:
        query = query.select(*[vehicle[field].as_(field) for field in fields])

    # Vehicle filters
    for field, value in filters.items():
        query = query.where(vehicle[field] == value)

    # Customer email filter
    if email:
        query = query.where(customer.email_id == email)

    return query.run(as_dict=True)
