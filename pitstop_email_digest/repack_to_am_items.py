"""
Repack stock of existing items into new "AM" (aftermarket) items, in ONE Stock Entry.

For every row in DATA:
  1. Fill `balance_qty` from the warehouses holding `existing_item_code`, deepest
     holding first. One warehouse covers the row on its own where it can; where it
     cannot, the row is spread over as many warehouses as it takes.
  2. If the item's total free stock cannot cover `balance_qty` (compared in stock
     UOM), skip the row - it is all-or-nothing, never a part delivery.
  3. Create `new_item_code` if it does not exist - a copy of `existing_item_code`
     (same item group, same UOM, same everything) with part_type = "AM".

Every slice becomes a repack pair in a SINGLE Repack Stock Entry:
     - `existing_item_code`  out of that warehouse, qty = the slice
     - `new_item_code`       into that warehouse,   qty = the slice, at `valuation_rate`

Stock already claimed by an earlier row of the same run is subtracted before the next
row is allocated, so two rows drawing on the same item can never overdraw a warehouse.

`valuation_rate` is optional and is per STOCK UOM. When given it is written to the new
item's row as a manual rate, so ERPNext does not overwrite it. When it is omitted the
row falls back to the existing item's current valuation rate in that warehouse, which
repacks the stock at unchanged value.

Every finished-goods row is marked `set_basic_rate_manually`. That matters in a combined
entry: left to itself, Repack pools the cost of ALL consumed rows and spreads it over ALL
produced rows, so one item's cost would leak into another item's rate.

Header fields (company, branch, cost center, workshop division) are per Stock Entry, not
per row. Slices that resolve to a different combination cannot share an entry, so they are
split into one entry per combination - the run prints it when that happens. A single input
row spread over warehouses in different branches therefore lands in more than one entry.

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
    False  # True -> ignore Warehouse.is_bin locations when allocating
)
# balance_qty is filled from the warehouses holding the item, deepest first. False lets an
# allocation empty a warehouse completely; True makes every warehouse keep MIN_REMAINDER
# back, which is the stricter rule the single-warehouse version of this script used.
REQUIRE_SURPLUS = False
MIN_REMAINDER = 1  # stock UOM units held back per warehouse when REQUIRE_SURPLUS is on
QTY_PRECISION = 9  # matches the 21,9 decimals Bin and Stock Entry Detail store
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

# Warehouses can restrict who may transact with them (restrict_to_users / restrict_to_roles,
# inherited from parent warehouses), and spreading a row over several warehouses makes it far
# more likely to touch one the item-creating user is barred from. Administrator is exempt from
# that check but is barred from creating Items, so the two jobs may need different users: set
# STOCK_ENTRY_USER to post the Stock Entries as someone else. None = the same user throughout.
STOCK_ENTRY_USER = None

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
        "new_item_code": 366101781,
        "existing_item_code": "100180",
        "uom": "Pcs",
        "balance_qty": 80,
        "valuation_rate": 10.08,
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


def can_transact_with(warehouse, user):
    """ERPNext's own warehouse restriction check, as a predicate."""
    from erpnext.stock.doctype.warehouse.warehouse import (
        check_warehouse_transaction_permission,
    )

    try:
        check_warehouse_transaction_permission(warehouse, user)
        return True
    except frappe.ValidationError:
        # the check reports by throwing; drop its message so it is not replayed later
        frappe.clear_last_message()
        return False


def get_stock_by_warehouse(item_code):
    """Every warehouse holding `item_code`, largest holding first (stock UOM).

    Ordered by quantity so an allocation drains the deepest bins before it reaches
    for the shallow ones, which keeps the number of Stock Entry rows down and the
    leftovers in fewer places. Warehouse name breaks ties so a run is repeatable.
    """
    conditions = ["b.item_code = %(item_code)s", "b.actual_qty > 0", "w.disabled = 0"]
    values = {"item_code": item_code}

    if COMPANY:
        conditions.append("w.company = %(company)s")
        values["company"] = COMPANY

    if EXCLUDE_BIN_WAREHOUSES:
        conditions.append("ifnull(w.is_bin, 0) = 0")

    return frappe.db.sql(
        """
		select b.warehouse, b.actual_qty, b.stock_uom, w.company
		from tabBin b
		inner join tabWarehouse w on w.name = b.warehouse
		where {conditions}
		order by b.actual_qty desc, b.warehouse asc
	""".format(conditions=" and ".join(conditions)),
        values,
        as_dict=1,
    )


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


def allocate(item_code, balance_qty, conversion_factor, claimed):
    """Split `balance_qty` across the warehouses holding the item, deepest first.

    Returns (allocations, available_stock_qty, required_stock_qty). `allocations` is
    empty when the item's total free stock cannot cover the row; the caller reports
    the shortfall from the two totals. Quantities come back in the row's UOM, and
    the last slice takes whatever is left so the slices always re-add to exactly
    `balance_qty` however awkward the conversion factor.
    """
    required_stock_qty = balance_qty * conversion_factor
    bins = get_stock_by_warehouse(item_code)

    # stock already spoken for by earlier rows of this same run
    free = []
    available_stock_qty = 0.0
    for b in bins:
        spare = flt(b.actual_qty) - claimed.get((item_code, b.warehouse), 0.0)
        if REQUIRE_SURPLUS:
            # never empty a warehouse: the deepest slice must still leave stock behind
            spare = spare - MIN_REMAINDER
        if spare > 0:
            available_stock_qty += spare
            free.append((b, spare))

    if available_stock_qty < required_stock_qty:
        return [], available_stock_qty, required_stock_qty

    allocations = []
    remaining_stock = required_stock_qty
    allocated_uom = 0.0

    for b, spare in free:
        if remaining_stock <= 0:
            break

        take_stock = min(spare, remaining_stock)
        take_uom = flt(take_stock / conversion_factor, QTY_PRECISION)
        if take_uom <= 0:
            continue

        remaining_stock -= take_stock
        # the closing slice absorbs any rounding drift, so the slices total balance_qty
        if remaining_stock <= 0:
            take_uom = flt(balance_qty - allocated_uom, QTY_PRECISION)
            if take_uom <= 0:
                break

        allocated_uom += take_uom
        allocations.append((b, take_uom, take_uom * conversion_factor))

    return allocations, available_stock_qty, required_stock_qty


def build_plan(data, posting_user):
    """Resolve every row to one or more warehouses, or to a reason for skipping.

    A row that no single warehouse can fill is spread over several, so one input row
    can produce several repack pairs - each with its own warehouse, branch and cost
    centre, and therefore potentially in different Stock Entries.
    """
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

        # fill balance_qty from the warehouses holding the item, deepest first
        allocations, available, required = allocate(
            existing_item_code, balance_qty, conversion_factor, claimed
        )

        if not allocations:
            stock_uom = frappe.get_cached_value("Item", existing_item_code, "stock_uom")
            if not available:
                skipped.append((label, "no stock in any warehouse"))
            else:
                skipped.append(
                    (
                        label,
                        "only {0} {1} free across all warehouses, {2} {1} needed{3}".format(
                            flt(available, QTY_PRECISION),
                            stock_uom,
                            flt(required, QTY_PRECISION),
                            " (earlier rows of this run already claimed some)"
                            if claimed
                            else "",
                        ),
                    )
                )
            continue

        row_plans = []
        shortfall = None

        for bin_row, take_uom, take_stock in allocations:
            if not can_transact_with(bin_row.warehouse, posting_user):
                shortfall = "{0} may not transact with {1} - set STOCK_ENTRY_USER, or grant access on the Warehouse".format(
                    posting_user, bin_row.warehouse
                )
                break

            branch = get_branch(bin_row.warehouse)
            if not branch:
                shortfall = (
                    "could not determine Branch for {0} - set DEFAULT_BRANCH".format(
                        bin_row.warehouse
                    )
                )
                break

            cost_center = get_cost_center(bin_row.warehouse, bin_row.company)
            if not cost_center:
                shortfall = "could not determine Cost Center for {0} - set DEFAULT_COST_CENTER".format(
                    bin_row.warehouse
                )
                break

            workshop_division = row.get("workshop_division") or get_workshop_division(
                bin_row.warehouse
            )
            if not workshop_division:
                shortfall = "could not determine Vehicle Workshop Division for {0} - set WORKSHOP_DIVISION".format(
                    bin_row.warehouse
                )
                break

            row_plans.append(
                {
                    "label": label,
                    "existing_item_code": existing_item_code,
                    "new_item_code": new_item_code,
                    "uom": uom,
                    "qty": take_uom,
                    "row_qty": balance_qty,
                    "stock_qty": take_stock,
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

        # a row is all-or-nothing: a slice we cannot post would under-deliver it
        if shortfall:
            skipped.append((label, shortfall))
            continue

        for plan in row_plans:
            key = (existing_item_code, plan["warehouse"])
            claimed[key] = claimed.get(key, 0.0) + plan["stock_qty"]

        plans.extend(row_plans)

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

    posting_user = STOCK_ENTRY_USER or frappe.session.user
    if posting_user != frappe.session.user:
        print("Stock Entries will be posted as {0}\n".format(posting_user))

    plans, skipped = build_plan(data, posting_user)

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

    by_row = {}
    for plan in plans:
        by_row.setdefault(plan["label"], []).append(plan)

    for label, row_plans in by_row.items():
        rate = row_plans[0]["valuation_rate"]
        head = "{0}: {1} {2} @ {3}".format(
            label,
            row_plans[0]["row_qty"],
            row_plans[0]["uom"],
            rate if rate is not None else "existing valuation rate",
        )
        if len(row_plans) == 1:
            plan = row_plans[0]
            print(
                "{0} - all from {1} (stock there {2} {3})".format(
                    head, plan["warehouse"], plan["available_qty"], plan["stock_uom"]
                )
            )
        else:
            print("{0} - split across {1} warehouses:".format(head, len(row_plans)))
            for plan in row_plans:
                print(
                    "      {0} {1} from {2} (stock there {3} {4})".format(
                        plan["qty"],
                        plan["uom"],
                        plan["warehouse"],
                        plan["available_qty"],
                        plan["stock_uom"],
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
            "Would create {0} Stock Entry(s) covering {1} repack pair(s) for {2} row(s).".format(
                len(groups), len(plans), len(by_row)
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

    item_user = frappe.session.user
    if posting_user != item_user:
        frappe.set_user(posting_user)

    try:
        _post_entries(groups, failed_items, submit, entries, failed)
    finally:
        if posting_user != item_user:
            frappe.set_user(item_user)

    _summarise(created_items, entries, skipped, failed)

    return {
        "created_items": created_items,
        "stock_entries": entries,
        "skipped": skipped,
        "failed": [label for label, _ in failed],
    }


def _post_entries(groups, failed_items, submit, entries, failed):
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
