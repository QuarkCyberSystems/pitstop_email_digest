"""
Create DRAFT Stock Reconciliation(s) that reset the valuation rate of given items
in every warehouse where they currently hold stock.

Nothing is submitted - the drafts are left for manual review/submit.

Lives in apps/pitstop_email_digest/pitstop_email_digest/ (symlinked at the bench root) because
`bench execute` only imports modules that sit inside an installed app.

Usage (dry run first, nothing is written):
	bench --site site_polaris execute pitstop_email_digest.stock_reco_valuation_rate.run

Create the drafts:
	bench --site site_polaris execute pitstop_email_digest.stock_reco_valuation_rate.run --kwargs "{'dry_run': False}"

Set COMPANY / POSTING_DATE / POSTING_TIME / DIMENSIONS below (or pass the same names
as kwargs to run(), which wins over the values in the file).

Options:
	company     restrict to warehouses of this company - None covers every company
	posting_date / posting_time    None = today / now
	branch      shortcut for DIMENSIONS["branch"]
	dimensions  accounting dimensions set on the document and on every row
	cost_center / expense_account  overrides - left None, ERPNext picks the company defaults
	match_on    how the values in DATA are looked up - "item_code" (default), "part_no",
	            "oe_no", or "auto" (item code, then Part No, then OE No)
	allow_multiple  when a Part No / OE No matches several items, apply the rate to all
	                of them instead of skipping the value
	group_by    "company" (one draft per company, chunked) or "warehouse"

	bench --site site_polaris execute pitstop_email_digest.stock_reco_valuation_rate.run --kwargs "{'dry_run': False, 'company': 'Pitstop Automotive Services LLC', 'posting_date': '2026-09-18', 'branch': 'Al Quoz', 'dimensions': {'vehicle_workshop_division': 'Mechanical'}}"

Or from `bench --site site_polaris console`:
	from pitstop_email_digest.stock_reco_valuation_rate import run
	run(dry_run=False)
"""

import frappe
from erpnext.stock.doctype.batch.batch import get_batches
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos
from erpnext.stock.doctype.stock_reconciliation.stock_reconciliation import (
    get_item_details,
)
from frappe.utils import cint, flt, nowtime, today

DATA = [
    {"item_code": "04152-37010", "rate": "24.58724138"},
    {"item_code": "04152-38010", "rate": "29.874"},
    {"item_code": "04465-0K580", "rate": "208"},
    {"item_code": "04465-26421", "rate": "261.3333333"},
    {"item_code": "04465-60280", "rate": "299.5"},
    {"item_code": "04466-26030", "rate": "163.81"},
    {"item_code": "08823-80250", "rate": "16.57142857"},
    {"item_code": "100180", "rate": "17.73911111"},
    {"item_code": "1109.AY", "rate": "36"},
    {"item_code": "1109AL", "rate": "42.14083333"},
    {"item_code": "11427953125", "rate": "47"},
    {"item_code": "16546-ED500", "rate": "45.66022222"},
    {"item_code": "16546-JG30A", "rate": "38.337"},
    {"item_code": "17801-0C010", "rate": "86"},
    {"item_code": "17801-0L040", "rate": "99.905"},
    {"item_code": "17801-38030", "rate": "99"},
    {"item_code": "17801-BZ150", "rate": "53"},
    {"item_code": "27277-1HDKE", "rate": "44.473"},
    {"item_code": "7850A002", "rate": "51.48"},
    {"item_code": "87139-52040", "rate": "107"},
    {"item_code": "88568-BZ060", "rate": "113.4645455"},
    {"item_code": "90915-10009", "rate": "32.09142857"},
    {"item_code": "90919-01191", "rate": "33"},
    {"item_code": "90919-01275", "rate": "44"},
    {"item_code": "90919-01289", "rate": "58"},
    {"item_code": "9809532380", "rate": "33"},
    {"item_code": "B7277-EG01A", "rate": "75.0325"},
    {"item_code": "D1060-1HA1A", "rate": "213.68"},
    {"item_code": "D4060-3JY0B", "rate": "131.7575"},
    {"item_code": "FL400S", "rate": "20.45"},
    {"item_code": "G1016056847", "rate": "29.6894964"},
    {"item_code": "G1017041361", "rate": "19.09"},
    {"item_code": "G1056025900", "rate": "47.36421053"},
    {"item_code": "G2032047000", "rate": "71.736"},
    {"item_code": "G8025530200", "rate": "33.40873016"},
    {"item_code": "G8025530600", "rate": "73.54"},
    {"item_code": "LR073669", "rate": "69.762"},
    {"item_code": "MZ691140", "rate": "12.241875"},
    {"item_code": "OSRAM-APO2825", "rate": "0.65"},
    {"item_code": "OSRAM-APO7506", "rate": "0.95"},
    {"item_code": "OSRAM-APO7507", "rate": "2.526190476"},
    {"item_code": "SHFL-910S", "rate": "25.6"},
]

# ---- set these (kwargs passed to run() override them) ----
COMPANY = "Pitstop Automotive Services LLC"  # e.g. "Pitstop Automotive Services LLC"; None = warehouses of every company
POSTING_DATE = None  # e.g. "2026-09-18"; None = today
POSTING_TIME = None  # e.g. "23:59:59"; None = now
COST_CENTER = "AutoWorks - PASLLC"  # None = company default
EXPENSE_ACCOUNT = "10110050 - Parts Stock Adjustments - PASLLC"  # difference account; None = company's Stock Adjustment Account

# accounting dimensions, set on the document and on every row
DIMENSIONS = {
    "vehicle_workshop_division": "Mechanical",
}


def _clean_dimensions(dimensions):
    """Keep only dimensions that exist on both the document and its items, and validate the links."""
    parent_meta = frappe.get_meta("Stock Reconciliation")
    child_meta = frappe.get_meta("Stock Reconciliation Item")

    out = {}
    for fieldname, value in (dimensions or {}).items():
        if value in (None, ""):
            continue

        field = parent_meta.get_field(fieldname)
        if not field:
            frappe.throw("Stock Reconciliation has no field " + fieldname)
        if not child_meta.get_field(fieldname):
            frappe.throw("Stock Reconciliation Item has no field " + fieldname)

        if field.fieldtype == "Link" and not frappe.db.exists(field.options, value):
            frappe.throw(field.options + " " + str(value) + " does not exist")

        out[fieldname] = value

    return out


def _resolve_items(code, match_on):
    """Return (item codes, the field the value was matched on)."""
    if match_on in ("auto", "item_code"):
        if frappe.db.exists("Item", code):
            return [code], "item_code"

    for field in ("part_no", "oe_no"):
        if match_on in ("auto", field):
            names = frappe.get_all(
                "Item", filters={field: code}, pluck="name", order_by="name"
            )
            if names:
                return names, field

    return [], None


def run(
    dry_run=True,
    data=None,
    company=None,
    posting_date=None,
    posting_time=None,
    branch=None,
    dimensions=None,
    cost_center=None,
    expense_account=None,
    match_on="item_code",
    allow_multiple=False,
    group_by="company",
    chunk_size=100,
    remarks="Valuation rate reset",
):
    """group_by: 'company' -> one draft per company (chunked), 'warehouse' -> one draft per warehouse."""
    rows = data or DATA
    company = company or COMPANY
    posting_date = posting_date or POSTING_DATE or today()
    posting_time = posting_time or POSTING_TIME or nowtime()
    cost_center = cost_center or COST_CENTER
    expense_account = expense_account or EXPENSE_ACCOUNT

    if company and not frappe.db.exists("Company", company):
        frappe.throw("Company " + str(company) + " does not exist")
    if cost_center and not frappe.db.exists("Cost Center", cost_center):
        frappe.throw("Cost Center " + str(cost_center) + " does not exist")
    if expense_account and not frappe.db.exists("Account", expense_account):
        frappe.throw("Account " + str(expense_account) + " does not exist")

    dimensions = dict(DIMENSIONS, **(dimensions or {}))
    if branch:
        dimensions["branch"] = branch
    dimensions = _clean_dimensions(dimensions)

    if dimensions:
        print("DIMS    " + ", ".join(k + "=" + str(v) for k, v in dimensions.items()))
    print(
        "SCOPE   company: "
        + (company or "all")
        + ", posting: "
        + str(posting_date)
        + " "
        + str(posting_time)
    )

    targets = {}
    for row in rows:
        code = row.get("item_code") or row.get("item_coe")
        rate = flt(row.get("rate"))
        if not code:
            print("SKIP    row without item code: " + str(row))
            continue

        item_codes, matched_on = _resolve_items(str(code).strip(), match_on)

        if not item_codes:
            print("SKIP    " + str(code) + ": no item found (tried " + match_on + ")")
            continue

        if matched_on != "item_code":
            print(
                "MATCH   "
                + str(code)
                + " -> "
                + matched_on
                + " of "
                + ", ".join(item_codes)
            )

        if len(item_codes) > 1 and not allow_multiple:
            print(
                "SKIP    "
                + str(code)
                + ": matches "
                + str(len(item_codes))
                + " items ("
                + ", ".join(item_codes)
                + "), pass allow_multiple=True to rate them all"
            )
            continue

        for item_code in item_codes:
            if item_code in targets and targets[item_code] != rate:
                print("SKIP    " + item_code + ": resolved twice with different rates")
                continue
            targets[item_code] = rate

    sr_items = []
    skipped = []

    for item_code, rate in targets.items():
        item = frappe.db.get_value(
            "Item",
            item_code,
            ["name", "is_stock_item", "disabled", "has_batch_no", "has_serial_no"],
            as_dict=True,
        )
        if not item:
            skipped.append(item_code + ": item does not exist")
            continue
        if cint(item.disabled):
            skipped.append(item_code + ": item is disabled")
            continue
        if not cint(item.is_stock_item):
            skipped.append(item_code + ": not a stock item")
            continue
        if rate <= 0:
            skipped.append(item_code + ": rate must be greater than zero")
            continue

        # every warehouse the item actually holds stock in
        bins = frappe.db.sql(
            """
			select bin.warehouse, bin.actual_qty, wh.company
			from `tabBin` bin
			join `tabWarehouse` wh on wh.name = bin.warehouse
			where bin.item_code = %(item_code)s and bin.actual_qty != 0
				and wh.is_group = 0 and ifnull(wh.disabled, 0) = 0
				{company_condition}
			order by wh.company, bin.warehouse
		""".format(company_condition="and wh.company = %(company)s" if company else ""),
            {"item_code": item_code, "company": company},
            as_dict=True,
        )

        if not bins:
            skipped.append(
                item_code
                + ": no stock in any warehouse"
                + (" of " + company if company else "")
            )
            continue

        for b in bins:
            if not b.company:
                skipped.append(
                    item_code + " @ " + b.warehouse + ": warehouse has no company"
                )
                continue

            # batch tracked items need one row per batch
            batch_nos = [None]
            if cint(item.has_batch_no):
                batch_nos = [
                    d.name
                    for d in get_batches(
                        item_code,
                        b.warehouse,
                        posting_date=posting_date,
                        posting_time=posting_time,
                        qty_condition="both",
                    )
                    if flt(d.qty)
                ]
                if not batch_nos:
                    skipped.append(
                        item_code + " @ " + b.warehouse + ": no batch with qty"
                    )
                    continue

            for batch_no in batch_nos:
                detail = get_item_details(
                    {
                        "company": b.company,
                        "posting_date": posting_date,
                        "posting_time": posting_time,
                        "item_code": item_code,
                        "warehouse": b.warehouse,
                        "batch_no": batch_no,
                        "reset_rate": 1,
                    }
                )

                where = (
                    item_code
                    + " @ "
                    + b.warehouse
                    + (" [" + batch_no + "]" if batch_no else "")
                )

                # qty must be written explicitly: this version computes total_qty before
                # a blank qty is backfilled on submit, which would wipe the stock out
                qty = flt(detail.get("current_qty"))
                if not qty:
                    skipped.append(where + ": current qty is zero")
                    continue

                serial_no = None
                if cint(item.has_serial_no):
                    serial_no = detail.get("current_serial_no") or ""
                    if len(get_serial_nos(serial_no)) != qty:
                        skipped.append(
                            where
                            + ": serial nos ("
                            + str(len(get_serial_nos(serial_no)))
                            + ") do not match qty ("
                            + str(qty)
                            + "), needs manual handling"
                        )
                        continue

                if flt(detail.get("current_valuation_rate")) == rate:
                    skipped.append(where + ": already at " + str(rate))
                    continue

                sr_items.append(
                    {
                        "company": b.company,
                        "warehouse": b.warehouse,
                        "item_code": item_code,
                        "item_name": detail.get("item_name"),
                        "batch_no": batch_no,
                        "qty": qty,
                        "serial_no": serial_no,
                        "valuation_rate": rate,
                        "current_valuation_rate": flt(
                            detail.get("current_valuation_rate")
                        ),
                        "cost_center": cost_center or detail.get("cost_center"),
                        "stock_uom": detail.get("stock_uom"),
                        "loose_uom": detail.get("stock_uom"),
                    }
                )

    for line in skipped:
        print("SKIP    " + line)

    if not sr_items:
        print("=== nothing to do ===")
        return []

    # group into documents
    groups = {}
    for row in sr_items:
        key = (
            (row["company"], row["warehouse"])
            if group_by == "warehouse"
            else (row["company"],)
        )
        groups.setdefault(key, []).append(row)

    chunk_size = cint(chunk_size) or 100
    created = []

    for key, items in sorted(groups.items()):
        doc_company = key[0]
        for start in range(0, len(items), chunk_size):
            chunk = items[start : start + chunk_size]

            if dry_run:
                print(
                    "[dry]   Stock Reconciliation for "
                    + " / ".join(key)
                    + " with "
                    + str(len(chunk))
                    + " row(s)"
                )
                for row in chunk:
                    print(
                        "[dry]     "
                        + row["item_code"]
                        + " @ "
                        + row["warehouse"]
                        + (" [" + row["batch_no"] + "]" if row["batch_no"] else "")
                        + ": qty "
                        + str(row["qty"])
                        + ", rate "
                        + str(row["current_valuation_rate"])
                        + " -> "
                        + str(row["valuation_rate"])
                    )
                continue

            try:
                sr = frappe.new_doc("Stock Reconciliation")
                sr.company = doc_company
                sr.purpose = "Stock Reconciliation"
                sr.set_posting_time = 1
                sr.posting_date = posting_date
                sr.posting_time = posting_time
                # without reset_rate the controller overwrites our rate with the current one
                sr.reset_rate = 1
                sr.remarks = remarks

                if cost_center:
                    sr.cost_center = cost_center
                if expense_account:
                    sr.expense_account = expense_account
                for fieldname, value in dimensions.items():
                    sr.set(fieldname, value)

                for row in chunk:
                    item_row = {
                        "item_code": row["item_code"],
                        "item_name": row["item_name"],
                        "warehouse": row["warehouse"],
                        "batch_no": row["batch_no"],
                        "qty": row["qty"],
                        "serial_no": row["serial_no"],
                        "valuation_rate": row["valuation_rate"],
                        "cost_center": row["cost_center"],
                        "stock_uom": row["stock_uom"],
                        "loose_uom": row["loose_uom"],
                        "loose_qty": 0,
                    }
                    item_row.update(dimensions)
                    sr.append("items", item_row)

                sr.insert()
                frappe.db.commit()
                created.append(sr.name)
                print(
                    "created "
                    + sr.name
                    + " ("
                    + " / ".join(key)
                    + ", "
                    + str(len(chunk))
                    + " row(s), "
                    "difference " + str(flt(sr.difference_amount, 2)) + ")"
                )
            except Exception as e:
                frappe.db.rollback()
                print("FAILED  " + " / ".join(key) + ": " + str(e))

    print(
        "=== "
        + ("dry run: " if dry_run else "finished: ")
        + str(len(sr_items))
        + " row(s), "
        + str(len(created))
        + " draft(s) created, "
        + str(len(skipped))
        + " skipped ==="
    )
    return created
