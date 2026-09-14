"""Move Target Settings / Target Details data into the new Target Role doctype."""

import frappe

MONTHS = (
    "january",
    "february",
    "march",
    "april",
    "may",
    "june",
    "july",
    "august",
    "september",
    "october",
    "november",
    "december",
)


def execute():
    migrate_targets()

    for doctype in ("Target Settings", "Target Details"):
        frappe.delete_doc("DocType", doctype, force=1, ignore_missing=True)


def migrate_targets():
    if not frappe.db.table_exists("Target Details"):
        return

    if not frappe.db.has_column("Target Details", "service_advisor"):
        return

    months = ", ".join(f"td.`{month}`" for month in MONTHS)
    rows = frappe.db.sql(
        f"""
		select
			td.service_advisor,
			td.year,
			{months}
		from
			`tabTarget Details` td
		where
			td.parent = 'Target Settings'
			and td.parenttype = 'Target Settings'
			and td.parentfield = 'service_advisor_targets'
			and td.service_advisor is not null
			and td.service_advisor != ''
		order by
			td.service_advisor, td.year
		""",
        as_dict=True,
    )

    if not rows:
        return

    grouped = {}
    for row in rows:
        grouped.setdefault(row.service_advisor, []).append(row)

    for sales_person, target_rows in grouped.items():
        if frappe.db.exists("Target Role", {"sales_person": sales_person}):
            continue

        employee = frappe.db.get_value(
            "Employee",
            {
                "user_id": frappe.db.get_value("Sales Person", sales_person, "user_id")
                or ""
            },
            ["name", "designation"],
            as_dict=True,
        )

        doc = frappe.new_doc("Target Role")
        doc.target_role_name = get_unique_name(sales_person)
        doc.sales_person = sales_person
        if employee:
            doc.employee = employee.name
            doc.designation = employee.designation

        for row in target_rows:
            doc.append(
                "targets",
                {"year": row.year, **{month: row.get(month) for month in MONTHS}},
            )

        doc.insert(ignore_permissions=True)


def get_unique_name(sales_person):
    name = sales_person
    suffix = 1
    while frappe.db.exists("Target Role", name):
        suffix += 1
        name = f"{sales_person} - {suffix}"

    return name
