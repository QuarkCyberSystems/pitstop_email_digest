"""Merge warehouse quantities of duplicate part numbers in a list of dicts.

The input is a list of dictionaries, each holding ``item_code``, ``part_no``,
``rate`` and ``warehouses`` (warehouse -> qty). Rows are walked in order and
grouped by ``part_no``:

* same ``item_code`` **and** ``part_no`` as a row already seen -> the same item,
  nothing is merged.
* different ``item_code`` but the same ``part_no`` -> another item code for the
  same part. Its warehouse quantities are added into the first row of that part
  (creating the warehouse there when missing) and zeroed on the current row, so
  the stock ends up consolidated under the first item code.

Example::

    [
        {"item_code": "PART-001", "part_no": "PART-001", "rate": 100,
         "warehouses": [{"WH-A": 10, "WH-B": 5}]},
        {"item_code": "XYZ", "part_no": "PART-001", "rate": 100,
         "warehouses": [{"WH-A": 3, "WH-C": 7}]},
    ]

becomes ``PART-001`` with ``{"WH-A": 13, "WH-B": 5, "WH-C": 7}`` and ``XYZ``
with ``{"WH-A": 0, "WH-C": 0}``.

Usage::

    bench --site <site> execute \
        pitstop_email_digest.utils.stock_reconciliation.stock_reconciliation.merge_warehouse_quantities \
        --kwargs "{'items': [...]}"
"""

import copy
import json

import frappe
from frappe import _
from frappe.utils import flt


def _load(items):
    """Accept the payload as a list or as a JSON string (whitelisted calls)."""
    if isinstance(items, str):
        items = json.loads(items)

    if isinstance(items, dict):
        items = [items]

    if not isinstance(items, list):
        frappe.throw(_("Items must be a list of dictionaries"))

    return items


def _normalize_warehouses(warehouses):
    """Return an ordered ``{warehouse: qty}`` dict from the accepted shapes.

    Handles a list of ``{warehouse: qty}`` dicts (the documented shape), a plain
    ``{warehouse: qty}`` dict, and a list of ``{"warehouse": .., "qty": ..}``
    rows. Repeated warehouses within one row are summed.
    """
    if not warehouses:
        return {}

    if isinstance(warehouses, str):
        warehouses = json.loads(warehouses)

    if isinstance(warehouses, dict):
        warehouses = [warehouses]

    normalized = {}
    for entry in warehouses:
        if not isinstance(entry, dict):
            frappe.throw(_("Unsupported warehouses entry: {0}").format(entry))

        if "warehouse" in entry:
            entry = {entry.get("warehouse"): entry.get("qty")}

        for warehouse, qty in entry.items():
            if not warehouse:
                continue
            normalized[warehouse] = flt(normalized.get(warehouse)) + flt(qty)

    return normalized


@frappe.whitelist()
def merge_warehouse_quantities(items):
    """Merge warehouse quantities of duplicate part numbers into the first row.

    Returns a new list in the input order, keeping each row's ``warehouses``
    shape: a plain ``{warehouse: qty}`` dict stays a dict, a list stays a list
    holding a single dict. The input is not modified.
    """
    rows = []
    warehouses_was_list = []
    for item in _load(items):
        row = copy.deepcopy(item)
        warehouses_was_list.append(isinstance(item.get("warehouses"), (list, tuple)))
        row["warehouses"] = _normalize_warehouses(item.get("warehouses"))
        rows.append(row)

    first_row_of_part = {}
    seen_items = set()

    for row in rows:
        item_code = row.get("item_code")
        part_no = row.get("part_no")

        if not item_code:
            frappe.throw(_("item_code is required for every row"))

        # fall back to the item code so rows without a part number stay distinct
        part_key = part_no or item_code

        if (item_code, part_key) in seen_items:
            # same item repeated - nothing to merge
            continue

        seen_items.add((item_code, part_key))

        target = first_row_of_part.get(part_key)
        if target is None:
            first_row_of_part[part_key] = row
            continue

        # another item code for the same part number
        target_warehouses = target["warehouses"]
        for warehouse, qty in row["warehouses"].items():
            target_warehouses[warehouse] = flt(target_warehouses.get(warehouse)) + flt(
                qty
            )
            row["warehouses"][warehouse] = 0

    for row, was_list in zip(rows, warehouses_was_list):
        if was_list:
            row["warehouses"] = [row["warehouses"]]

    return rows
