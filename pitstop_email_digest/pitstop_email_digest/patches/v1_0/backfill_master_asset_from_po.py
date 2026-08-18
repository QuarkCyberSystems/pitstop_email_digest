"""Backfill Master Asset links for existing Assets that have a resolvable Purchase Order.

Assets without a resolvable PO are left untouched (user assigns them manually).
Idempotent — safe to re-run.
"""

import frappe

from pitstop_email_digest.overrides.asset.asset_hooks import (
    _get_or_create_master_asset_for_po,
    _refresh_master_asset,
    resolve_purchase_order,
)

BATCH_SIZE = 500


def execute():
    # Only submitted Assets are eligible for Master Asset linking.
    assets = frappe.get_all(
        "Asset",
        filters={"master_asset": ("in", ["", None]), "docstatus": 1},
        fields=["name"],
        order_by="creation asc",
    )
    total = len(assets)
    print(f"[master-asset backfill] scanning {total} unlinked submitted assets...")

    touched_mas: set[str] = set()
    linked = no_po = failed = 0

    for i, row in enumerate(assets, start=1):
        try:
            asset = frappe.get_doc("Asset", row.name)
            po = asset.get("purchase_order") or resolve_purchase_order(asset)

            if not po:
                no_po += 1
                continue

            ma_name = _get_or_create_master_asset_for_po(po, asset)
            if not ma_name:
                failed += 1
                continue

            frappe.db.set_value(
                "Asset", row.name, "master_asset", ma_name, update_modified=False
            )
            if asset.get("purchase_order") != po:
                frappe.db.set_value(
                    "Asset", row.name, "purchase_order", po, update_modified=False
                )

            touched_mas.add(ma_name)
            linked += 1

        except Exception as e:
            failed += 1
            frappe.log_error(
                title="Master Asset backfill failed",
                message=f"Asset: {row.name}\n{frappe.get_traceback()}",
            )

        if i % BATCH_SIZE == 0:
            frappe.db.commit()
            print(
                f"[master-asset backfill] processed {i}/{total} (linked={linked}, no_po={no_po}, failed={failed})"
            )

    # Refresh totals/status for every MA we touched.
    print(
        f"[master-asset backfill] refreshing {len(touched_mas)} touched Master Assets..."
    )
    for ma_name in touched_mas:
        try:
            _refresh_master_asset(ma_name)
        except Exception:
            frappe.log_error(
                title="Master Asset refresh failed",
                message=f"MA: {ma_name}\n{frappe.get_traceback()}",
            )

    frappe.db.commit()
    print(
        f"[master-asset backfill] done. total={total} linked={linked} no_po={no_po} failed={failed}"
    )
