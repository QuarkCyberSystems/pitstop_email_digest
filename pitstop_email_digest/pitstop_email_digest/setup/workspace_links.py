import frappe

WORKSPACE = "Workshop"
CARD = "Billing Reports"
REPORT = "RO Sold Hours"

LINK_FIELDS = (
    "type",
    "label",
    "icon",
    "hidden",
    "link_type",
    "link_to",
    "dependencies",
    "only_for",
    "onboard",
    "is_query_report",
    "link_count",
    "description",
    "report_ref_doctype",
)


def add_ro_sold_hours_to_workshop():
    """Add the RO Sold Hours report to the Billing Reports card of the Workshop workspace.

    The Workshop workspace is owned by the `automotive` app, which re-imports it on every
    migrate and overwrites its links. Running this on `after_migrate` re-applies the link.
    """
    if not frappe.db.exists("Workspace", WORKSPACE) or not frappe.db.exists(
        "Report", REPORT
    ):
        return

    doc = frappe.get_doc("Workspace", WORKSPACE)
    rows = [{field: link.get(field) for field in LINK_FIELDS} for link in doc.links]

    card_idx = next(
        (
            i
            for i, row in enumerate(rows)
            if row["type"] == "Card Break" and row["label"] == CARD
        ),
        None,
    )
    if card_idx is None:
        return

    link_count = int(rows[card_idx].get("link_count") or 0)
    card_links = rows[card_idx + 1 : card_idx + 1 + link_count]

    if any(row.get("link_to") == REPORT for row in card_links):
        return

    rows.insert(
        card_idx + 1 + link_count,
        {
            "type": "Link",
            "label": REPORT,
            "hidden": 0,
            "link_type": "Report",
            "link_to": REPORT,
            "onboard": 0,
            "is_query_report": 1,
            "link_count": 0,
        },
    )
    rows[card_idx]["link_count"] = link_count + 1

    doc.set("links", [])
    for row in rows:
        doc.append("links", row)

    doc.save(ignore_permissions=True)
