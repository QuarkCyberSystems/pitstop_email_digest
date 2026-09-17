"""
Repack stock of existing items into new "AM" (aftermarket) items, in ONE Stock Entry.

For every row in DATA:
  1. Find the warehouse holding the MAXIMUM qty of `existing_item_code`.
  2. If that qty is greater than `balance_qty` (compared in stock UOM), continue,
     otherwise skip the row.
  3. Create `new_item_code` if it does not exist - a copy of `existing_item_code`
     (same item group, same UOM, same everything) with part_type = "AM".

All surviving rows then go into a SINGLE Repack Stock Entry, two rows per pair:
     - `existing_item_code`  out of the warehouse, qty = balance_qty
     - `new_item_code`       into the warehouse,   qty = balance_qty, at `valuation_rate`

`valuation_rate` is optional and is per STOCK UOM. When given it is written to the new
item's row as a manual rate, so ERPNext does not overwrite it. When it is omitted the
row falls back to the existing item's current valuation rate in that warehouse, which
repacks the stock at unchanged value.

Every finished-goods row is marked `set_basic_rate_manually`. That matters in a combined
entry: left to itself, Repack pools the cost of ALL consumed rows and spreads it over ALL
produced rows, so one item's cost would leak into another item's rate.

Header fields (company, branch, cost center) are per Stock Entry, not per row. Rows that
resolve to a different company/branch/cost center cannot share an entry, so they are split
into one entry per combination - the run prints it when that happens.

Usage:
Fill in DATA below, then from the bench directory:

    bench --site site_polaris execute pitstop_email_digest.repack_to_am_items.run \
        --kwargs "{'dry_run': True}"

    bench --site site_polaris execute pitstop_email_digest.repack_to_am_items.run \
        --kwargs "{'dry_run': False, 'submit': True, 'as_user': 'zahid.gul@pitstop360.com'}"

`--kwargs` is eval'd as a Python literal, so the rows can be passed inline instead of
editing DATA - mind the quoting, the whole thing is one shell argument:

    bench --site site_polaris execute pitstop_email_digest.repack_to_am_items.run \
        --kwargs "{'dry_run': True, 'data': [{'existing_item_code': 'ABC', 'new_item_code': 'ABC-AM', 'uom': 'Pcs', 'balance_qty': 5, 'valuation_rate': 99.5}]}"

Or from `bench --site site_polaris console`:

    from pitstop_email_digest.repack_to_am_items import run
    run(dry_run=True)

`as_user` is needed whenever a new item has to be created: the "Item Creation Or Updation"
server script rejects the save unless the session user holds the "Parts Item Updation" role,
and it reads `tabHas Role` directly, so Administrator is not exempt.
"""

import frappe
from frappe.utils import flt, nowdate

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

DRY_RUN = True  # True -> report only, nothing is written
SUBMIT = False  # False -> the Stock Entry is left in draft
COMPANY = None  # restrict the warehouse search to one company; None = any
EXCLUDE_BIN_WAREHOUSES = (
    False  # True -> ignore Warehouse.is_bin locations when picking the max warehouse
)
DEFAULT_BRANCH = None  # fallback Branch when it cannot be derived from the warehouse
DEFAULT_COST_CENTER = (
    None  # fallback Cost Center when it cannot be derived from the warehouse
)
# `Vehicle Workshop Division` is an Accounting Dimension flagged mandatory for both P&L and
# Balance Sheet accounts, so every GL entry this script posts needs one. Repacking at an
# explicit valuation_rate moves value, which means real GL entries - unlike a value-neutral
# repack, where everything nets to zero and no GL entry is written at all.
# Set it here (AutoCare / Mechanical / Body Shop / Car Care / Admin), or per row via
# "workshop_division". Left as None it is inferred from the warehouse's own posting history.
WORKSHOP_DIVISION = "Mechanical"
POSTING_DATE = None  # None -> today
NEW_ITEM_PART_TYPE = "AM"

# The "Item Creation Or Updation" server script refuses to save any stock Item unless the
# session user holds this role - and it reads `tabHas Role` directly, so Administrator is
# NOT exempt. Set AS_USER to a user that holds the role in order to create new items.
AS_USER = None
ITEM_CREATION_ROLE = "Parts Item Updation"

# Fields that must not be carried over to the new item.
# `barcodes` are globally unique, and the AM part is not a variant of the OE template.
ITEM_FIELDS_TO_CLEAR = {
    "variant_of": None,
    "has_variants": 0,
    "attributes": [],
    "barcodes": [],
    "last_purchase_rate": 0,
    "default_bom": None,
    "customer_code": None,
    "image": None,
}


DATA = [
    {
        "new_item_code": 366100611,
        "existing_item_code": "04152-37010",
        "uom": "Pcs",
        "balance_qty": 2,
        "valuation_rate": 11.9,
    },
    {
        "new_item_code": 366100731,
        "existing_item_code": "04152-38010",
        "uom": "Pcs",
        "balance_qty": 28,
        "valuation_rate": 14.54,
    },
    {
        "new_item_code": 355014121,
        "existing_item_code": "04465-0K580",
        "uom": "Nos",
        "balance_qty": 3,
        "valuation_rate": 107.99,
    },
    {
        "new_item_code": 355015831,
        "existing_item_code": "04465-26421",
        "uom": "Pcs",
        "balance_qty": 3,
        "valuation_rate": 122.11,
    },
    {
        "new_item_code": 355013151,
        "existing_item_code": "04465-60280",
        "uom": "Pcs",
        "balance_qty": 2,
        "valuation_rate": 149.91,
    },
    {
        "new_item_code": 355040131,
        "existing_item_code": "04466-26030",
        "uom": "Nos",
        "balance_qty": 1,
        "valuation_rate": 95.58,
    },
    {
        "new_item_code": 358288021,
        "existing_item_code": "08823-80250",
        "uom": "Pcs",
        "balance_qty": 15,
        "valuation_rate": 9.01,
    },
    {
        "new_item_code": 366101781,
        "existing_item_code": "100180",
        "uom": "Pcs",
        "balance_qty": 80,
        "valuation_rate": 10.08,
    },
    {
        "new_item_code": 366100031,
        "existing_item_code": "1109.AY",
        "uom": "Pcs",
        "balance_qty": 3,
        "valuation_rate": 8.68,
    },
    {
        "new_item_code": 366100111,
        "existing_item_code": "1109AL",
        "uom": "Nos",
        "balance_qty": 30,
        "valuation_rate": 5.33,
    },
    {
        "new_item_code": 366102701,
        "existing_item_code": "11427953125",
        "uom": "Pcs",
        "balance_qty": 2,
        "valuation_rate": 15.86,
    },
    {
        "new_item_code": 366130951,
        "existing_item_code": "16546-ED500",
        "uom": "Pcs",
        "balance_qty": 30,
        "valuation_rate": 21.81,
    },
    {
        "new_item_code": 366130351,
        "existing_item_code": "16546-JG30A",
        "uom": "Pcs",
        "balance_qty": 2,
        "valuation_rate": 17.43,
    },
    {
        "new_item_code": 366133861,
        "existing_item_code": "17801-0C010",
        "uom": "Pcs",
        "balance_qty": 1,
        "valuation_rate": 52.88,
    },
    {
        "new_item_code": 366132411,
        "existing_item_code": "17801-0L040",
        "uom": "Pcs",
        "balance_qty": 10,
        "valuation_rate": 59.76,
    },
    {
        "new_item_code": 366136401,
        "existing_item_code": "17801-38030",
        "uom": "Pcs",
        "balance_qty": 3,
        "valuation_rate": 25.84,
    },
    {
        "new_item_code": 366132851,
        "existing_item_code": "17801-BZ150",
        "uom": "Pcs",
        "balance_qty": 5,
        "valuation_rate": 17.45,
    },
    {
        "new_item_code": 366120971,
        "existing_item_code": "27277-1HDKE",
        "uom": "Pcs",
        "balance_qty": 100,
        "valuation_rate": 17.55,
    },
    {
        "new_item_code": 366123481,
        "existing_item_code": "7850A002",
        "uom": "Pcs",
        "balance_qty": 3,
        "valuation_rate": 14.81,
    },
    {
        "new_item_code": 366120051,
        "existing_item_code": "87139-52040",
        "uom": "Pcs",
        "balance_qty": 25,
        "valuation_rate": 13.22,
    },
    {
        "new_item_code": 366122311,
        "existing_item_code": "88568-BZ060",
        "uom": "Pcs",
        "balance_qty": 19,
        "valuation_rate": 15.1,
    },
    {
        "new_item_code": 366100131,
        "existing_item_code": "90915-10009",
        "uom": "Nos",
        "balance_qty": 4,
        "valuation_rate": 15.86,
    },
    {
        "new_item_code": 188706081,
        "existing_item_code": "90919-01191",
        "uom": "Pcs",
        "balance_qty": 8,
        "valuation_rate": 17.0,
    },
    {
        "new_item_code": 188705161,
        "existing_item_code": "90919-01275",
        "uom": "Pcs",
        "balance_qty": 20,
        "valuation_rate": 15.48,
    },
    {
        "new_item_code": 188869271,
        "existing_item_code": "90919-01289",
        "uom": "Pcs",
        "balance_qty": 4,
        "valuation_rate": 36.53,
    },
    {
        "new_item_code": 366100801,
        "existing_item_code": "9809532380",
        "uom": "Pcs",
        "balance_qty": 15,
        "valuation_rate": 20.62,
    },
    {
        "new_item_code": 366124371,
        "existing_item_code": "B7277-EG01A",
        "uom": "Pcs",
        "balance_qty": 10,
        "valuation_rate": 23.0,
    },
    {
        "new_item_code": 355015981,
        "existing_item_code": "D1060-1HA1A",
        "uom": "Pcs",
        "balance_qty": 1,
        "valuation_rate": 75.54,
    },
    {
        "new_item_code": 355020401,
        "existing_item_code": "D4060-3JY0B",
        "uom": "Pcs",
        "balance_qty": 1,
        "valuation_rate": 90.77,
    },
    {
        "new_item_code": 366101251,
        "existing_item_code": "FL400S",
        "uom": "Pcs",
        "balance_qty": 5,
        "valuation_rate": 10.82,
    },
    {
        "new_item_code": 366101811,
        "existing_item_code": "G1016056847",
        "uom": "Pcs",
        "balance_qty": 180,
        "valuation_rate": 16.8,
    },
    {
        "new_item_code": 742901051,
        "existing_item_code": "G1017041361",
        "uom": "Pcs",
        "balance_qty": 2,
        "valuation_rate": 5.88,
    },
    {
        "new_item_code": 366100511,
        "existing_item_code": "G1056025900",
        "uom": "Pcs",
        "balance_qty": 261,
        "valuation_rate": 11.1,
    },
    {
        "new_item_code": 366132191,
        "existing_item_code": "G2032047000",
        "uom": "Pcs",
        "balance_qty": 30,
        "valuation_rate": 26.44,
    },
    {
        "new_item_code": 366124221,
        "existing_item_code": "G8025530200",
        "uom": "Pcs",
        "balance_qty": 91,
        "valuation_rate": 21.48,
    },
    {
        "new_item_code": 366122101,
        "existing_item_code": "G8025530600",
        "uom": "Pcs",
        "balance_qty": 30,
        "valuation_rate": 43.62,
    },
    {
        "new_item_code": 366101511,
        "existing_item_code": "LR073669",
        "uom": "Pcs",
        "balance_qty": 3,
        "valuation_rate": 15.34,
    },
    {
        "new_item_code": 366100281,
        "existing_item_code": "MZ691140",
        "uom": "Pcs",
        "balance_qty": 99,
        "valuation_rate": 9.8,
    },
    {
        "new_item_code": 3594121,
        "existing_item_code": "OSRAM-APO2825",
        "uom": "Pcs",
        "balance_qty": 7,
        "valuation_rate": 0.53,
    },
    {
        "new_item_code": 2073121,
        "existing_item_code": "OSRAM-APO7506",
        "uom": "Pcs",
        "balance_qty": 8,
        "valuation_rate": 0.75,
    },
    {
        "new_item_code": 6841121,
        "existing_item_code": "OSRAM-APO7507",
        "uom": "Pcs",
        "balance_qty": 8,
        "valuation_rate": 35.0,
    },
    {
        "new_item_code": 366101211,
        "existing_item_code": "SHFL-910S",
        "uom": "Pcs",
        "balance_qty": 3,
        "valuation_rate": 13.53,
    },
]


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------


def can_create_items(user):
    """Mirrors the `Item Creation Or Updation` server script - it reads Has Role directly."""
    return bool(
        frappe.db.exists(
            "Has Role",
            {"parent": user, "parenttype": "User", "role": ITEM_CREATION_ROLE},
        )
    )


def get_max_qty_warehouse(item_code):
    """Warehouse holding the largest actual_qty of `item_code` (stock UOM)."""
    conditions = ["b.item_code = %(item_code)s", "b.actual_qty > 0", "w.disabled = 0"]
    values = {"item_code": item_code}

    if COMPANY:
        conditions.append("w.company = %(company)s")
        values["company"] = COMPANY

    if EXCLUDE_BIN_WAREHOUSES:
        conditions.append("ifnull(w.is_bin, 0) = 0")

    rows = frappe.db.sql(
        """
		select b.warehouse, b.actual_qty, b.stock_uom, w.company
		from tabBin b
		inner join tabWarehouse w on w.name = b.warehouse
		where {conditions}
		order by b.actual_qty desc, b.warehouse asc
		limit 1
	""".format(conditions=" and ".join(conditions)),
        values,
        as_dict=1,
    )

    return rows[0] if rows else None


def get_common_value(warehouse, fieldname):
    """Value most often used with this warehouse on submitted Stock Entries.

    Neither Branch nor Cost Center is linked to Warehouse in the schema, so they are
    inferred from how this warehouse has actually been posted in the past.
    """
    row = frappe.db.sql(
        """
		select se.`{fieldname}` as value, count(*) as cnt
		from `tabStock Entry Detail` sed
		inner join `tabStock Entry` se on se.name = sed.parent
		where se.docstatus = 1
			and ifnull(se.`{fieldname}`, '') != ''
			and %(warehouse)s in (ifnull(sed.s_warehouse, ''), ifnull(sed.t_warehouse, ''))
		group by se.`{fieldname}`
		order by cnt desc
		limit 1
	""".format(fieldname=fieldname),
        {"warehouse": warehouse},
        as_dict=1,
    )

    return row[0].value if row else None


def get_branch(warehouse):
    return get_common_value(warehouse, "branch") or DEFAULT_BRANCH


def get_workshop_division(warehouse):
    """Mandatory accounting dimension - see WORKSHOP_DIVISION above."""
    return WORKSHOP_DIVISION or get_common_value(warehouse, "vehicle_workshop_division")


def get_cost_center(warehouse, company):
    """Cost Center for the entry - mandatory because the stock adjustment account is P&L."""
    return (
        get_common_value(warehouse, "cost_center")
        or DEFAULT_COST_CENTER
        or frappe.get_cached_value("Company", company, "cost_center")
    )


def get_conversion_factor(item_code, uom):
    """Factor converting `uom` into the item's stock UOM. None if not convertible."""
    from erpnext.stock.doctype.stock_entry.stock_entry import get_uom_details

    stock_uom = frappe.get_cached_value("Item", item_code, "stock_uom")
    if uom == stock_uom:
        return 1.0

    details = get_uom_details(item_code, uom, 1)
    if details.get("not_convertible") or not flt(details.get("conversion_factor")):
        return None

    return flt(details["conversion_factor"])


# ---------------------------------------------------------------------------
# Writes
# ---------------------------------------------------------------------------


def create_new_item(existing_item_code, new_item_code):
    """Copy of the existing item with part_type = AM."""
    source = frappe.get_doc("Item", existing_item_code)
    new_item = frappe.copy_doc(source)

    new_item.item_code = new_item_code
    new_item.part_type = NEW_ITEM_PART_TYPE

    for fieldname, value in ITEM_FIELDS_TO_CLEAR.items():
        new_item.set(fieldname, value)

    new_item.insert()
    return new_item


def make_repack_entry(plans, branch, cost_center, workshop_division, company):
    """One Repack Stock Entry holding every pair in `plans`."""
    se = frappe.new_doc("Stock Entry")
    se.company = company
    se.stock_entry_type = "Repack"
    se.purpose = "Repack"
    se.branch = branch
    se.cost_center = cost_center
    se.vehicle_workshop_division = workshop_division
    se.posting_date = POSTING_DATE or nowdate()
    if POSTING_DATE:
        se.set_posting_time = 1

    for plan in plans:
        args = {
            "uom": plan["uom"],
            "qty": plan["qty"],
            "warehouse": plan["warehouse"],
            "company": company,
        }

        source_details = se.get_item_details(
            dict(args, item_code=plan["existing_item_code"])
        )
        source_row = se.append("items", {})
        source_row.update(source_details)
        source_row.item_code = plan["existing_item_code"]
        source_row.qty = plan["qty"]
        source_row.uom = plan["uom"]
        source_row.s_warehouse = plan["warehouse"]
        source_row.t_warehouse = None
        source_row.cost_center = source_row.cost_center or cost_center
        source_row.vehicle_workshop_division = workshop_division

        target_details = se.get_item_details(
            dict(args, item_code=plan["new_item_code"])
        )
        target_row = se.append("items", {})
        target_row.update(target_details)
        target_row.item_code = plan["new_item_code"]
        target_row.qty = plan["qty"]
        target_row.uom = plan["uom"]
        target_row.s_warehouse = None
        target_row.t_warehouse = plan["warehouse"]
        target_row.cost_center = target_row.cost_center or cost_center
        target_row.vehicle_workshop_division = workshop_division

        # Pin the rate, otherwise Repack pools every consumed row's cost across every
        # produced row and the items in this entry contaminate each other's valuation.
        rate = plan["valuation_rate"]
        target_row.basic_rate = (
            flt(rate) if rate is not None else flt(source_details.get("basic_rate"))
        )
        target_row.set_basic_rate_manually = 1

    se.insert()
    return se


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


def build_plan(data):
    """Resolve every row to a warehouse/branch/cost centre, or to a reason for skipping."""
    plans, skipped = [], []
    claimed = {}  # (item_code, warehouse) -> stock qty already claimed by earlier rows

    for idx, row in enumerate(data, start=1):
        existing_item_code = row["existing_item_code"]
        new_item_code = row["new_item_code"]
        uom = row["uom"]
        balance_qty = flt(row["balance_qty"])
        label = "{0}. {1} -> {2}".format(idx, existing_item_code, new_item_code)

        if not frappe.db.exists("Item", existing_item_code):
            skipped.append((label, "existing item not found"))
            continue

        if balance_qty <= 0:
            skipped.append((label, "balance_qty is {0}".format(balance_qty)))
            continue

        existing_item = frappe.get_cached_doc("Item", existing_item_code)

        if existing_item.has_serial_no or existing_item.has_batch_no:
            skipped.append(
                (
                    label,
                    "item is serialized/batched - repack needs serial/batch selection",
                )
            )
            continue

        conversion_factor = get_conversion_factor(existing_item_code, uom)
        if conversion_factor is None:
            skipped.append(
                (label, "UOM {0} is not convertible for this item".format(uom))
            )
            continue

        # 1. warehouse holding the most stock
        bin_row = get_max_qty_warehouse(existing_item_code)
        if not bin_row:
            skipped.append((label, "no stock in any warehouse"))
            continue

        # 2. is that stock greater than balance_qty? Earlier rows drawing on the same
        #    warehouse are counted too - one entry cannot overdraw a bin twice.
        required_stock_qty = balance_qty * conversion_factor
        key = (existing_item_code, bin_row.warehouse)
        already_claimed = claimed.get(key, 0.0)
        if flt(bin_row.actual_qty) <= already_claimed + required_stock_qty:
            skipped.append(
                (
                    label,
                    "max stock {0} {1} in {2} does not cover {3} {1}{4}".format(
                        flt(bin_row.actual_qty),
                        bin_row.stock_uom,
                        bin_row.warehouse,
                        required_stock_qty,
                        " (+{0} {1} already claimed by earlier rows)".format(
                            already_claimed, bin_row.stock_uom
                        )
                        if already_claimed
                        else "",
                    ),
                )
            )
            continue

        branch = get_branch(bin_row.warehouse)
        if not branch:
            skipped.append(
                (
                    label,
                    "could not determine Branch for {0} - set DEFAULT_BRANCH".format(
                        bin_row.warehouse
                    ),
                )
            )
            continue

        cost_center = get_cost_center(bin_row.warehouse, bin_row.company)
        if not cost_center:
            skipped.append(
                (
                    label,
                    "could not determine Cost Center for {0} - set DEFAULT_COST_CENTER".format(
                        bin_row.warehouse
                    ),
                )
            )
            continue

        workshop_division = row.get("workshop_division") or get_workshop_division(
            bin_row.warehouse
        )
        if not workshop_division:
            skipped.append(
                (
                    label,
                    "could not determine Vehicle Workshop Division for {0} - set WORKSHOP_DIVISION".format(
                        bin_row.warehouse
                    ),
                )
            )
            continue

        claimed[key] = already_claimed + required_stock_qty

        plans.append(
            {
                "label": label,
                "existing_item_code": existing_item_code,
                "new_item_code": new_item_code,
                "uom": uom,
                "qty": balance_qty,
                "valuation_rate": row.get("valuation_rate"),
                "warehouse": bin_row.warehouse,
                "available_qty": flt(bin_row.actual_qty),
                "stock_uom": bin_row.stock_uom,
                "company": bin_row.company,
                "branch": branch,
                "cost_center": cost_center,
                "workshop_division": workshop_division,
                "item_group": existing_item.item_group,
                "item_exists": bool(frappe.db.exists("Item", new_item_code)),
            }
        )

    return plans, skipped


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def run(data=None, dry_run=None, submit=None, as_user=None):
    data = data if data is not None else DATA
    dry_run = DRY_RUN if dry_run is None else dry_run
    submit = SUBMIT if submit is None else submit
    as_user = as_user or AS_USER

    if not data:
        print("Nothing to do - DATA is empty.")
        return

    previous_user = frappe.session.user
    if as_user:
        frappe.set_user(as_user)

    try:
        return _run(data, dry_run, submit)
    finally:
        if as_user:
            frappe.set_user(previous_user)


def _run(data, dry_run, submit):
    print("DRY RUN - nothing will be written\n" if dry_run else "LIVE RUN\n")

    plans, skipped = build_plan(data)

    to_create = sorted({p["new_item_code"] for p in plans if not p["item_exists"]})
    if to_create and not can_create_items(frappe.session.user):
        print(
            "{0} new item codes have to be created, but {1} does not hold the '{2}' role, "
            "so no Item can be saved.\nRe-run with as_user set to a user that holds that role, "
            "e.g. run(as_user='someone@example.com').\n".format(
                len(to_create), frappe.session.user, ITEM_CREATION_ROLE
            )
        )
        if not dry_run:
            return

    for plan in plans:
        rate = plan["valuation_rate"]
        print(
            "{0}: {1} {2} in {3} (stock there {4} {5}) @ {6}".format(
                plan["label"],
                plan["qty"],
                plan["uom"],
                plan["warehouse"],
                plan["available_qty"],
                plan["stock_uom"],
                rate if rate is not None else "existing valuation rate",
            )
        )

    # Company, branch and cost centre live on the Stock Entry, not on its rows.
    groups = {}
    for plan in plans:
        groups.setdefault(
            (
                plan["company"],
                plan["branch"],
                plan["cost_center"],
                plan["workshop_division"],
            ),
            [],
        ).append(plan)

    if len(groups) == 1:
        company, branch, cost_center, division = list(groups)[0]
        print(
            "\nOne Stock Entry: {0} | branch {1} | cost centre {2} | division {3}".format(
                company, branch, cost_center, division
            )
        )
    elif len(groups) > 1:
        print(
            "\n{0} Stock Entries are needed - these rows do not share a company/branch/cost centre/division:".format(
                len(groups)
            )
        )
        for company, branch, cost_center, division in groups:
            print(
                "   {0} | {1} | {2} | {3}".format(
                    company, branch, cost_center, division
                )
            )

    if dry_run:
        print(
            "\nWould create {0} item(s): {1}".format(
                len(to_create), ", ".join(to_create) or "-"
            )
        )
        print(
            "Would create {0} Stock Entry(s) covering {1} repack pair(s).".format(
                len(groups), len(plans)
            )
        )
        _summarise([], [], skipped, [])
        return {"plans": plans, "skipped": skipped}

    created_items, entries, failed = [], [], []

    for new_item_code in to_create:
        existing_item_code = next(
            p["existing_item_code"]
            for p in plans
            if p["new_item_code"] == new_item_code
        )
        try:
            create_new_item(existing_item_code, new_item_code)
            created_items.append(new_item_code)
            frappe.db.commit()
            print("created Item {0}".format(new_item_code))
        except Exception:
            frappe.db.rollback()
            failed.append(("Item {0}".format(new_item_code), frappe.get_traceback()))
            print("Item {0}: FAILED\n{1}".format(new_item_code, frappe.get_traceback()))

    failed_items = {label.replace("Item ", "") for label, _ in failed}

    for (company, branch, cost_center, division), group_plans in groups.items():
        group_plans = [p for p in group_plans if p["new_item_code"] not in failed_items]
        if not group_plans:
            continue

        try:
            se = make_repack_entry(group_plans, branch, cost_center, division, company)
            if submit:
                se.submit()
            frappe.db.commit()

            entries.append(se.name)
            print(
                "\n{0} {1} - {2} pair(s), branch {3}, cost centre {4}, division {5}".format(
                    se.name,
                    "submitted" if submit else "draft",
                    len(group_plans),
                    branch,
                    cost_center,
                    division,
                )
            )
            print(
                "   in {0}, out {1}, difference {2}".format(
                    se.total_incoming_value,
                    se.total_outgoing_value,
                    se.value_difference,
                )
            )
        except Exception:
            frappe.db.rollback()
            label = "Stock Entry ({0} / {1} / {2})".format(
                branch, cost_center, division
            )
            failed.append((label, frappe.get_traceback()))
            print("{0}: FAILED\n{1}".format(label, frappe.get_traceback()))

    _summarise(created_items, entries, skipped, failed)

    return {
        "created_items": created_items,
        "stock_entries": entries,
        "skipped": skipped,
        "failed": [label for label, _ in failed],
    }


def _summarise(created_items, entries, skipped, failed):
    print("\n" + "=" * 60)
    print("Items created : {0}".format(len(created_items)))
    print("Stock Entries : {0}".format(len(entries)))
    print("Skipped       : {0}".format(len(skipped)))
    print("Failed        : {0}".format(len(failed)))

    for label, reason in skipped:
        print("  SKIPPED {0} - {1}".format(label, reason))
    for label, _ in failed:
        print("  FAILED  {0}".format(label))
