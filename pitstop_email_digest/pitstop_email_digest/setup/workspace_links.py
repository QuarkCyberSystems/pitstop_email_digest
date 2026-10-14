import frappe

WORKSPACE = "Workshop"

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
    add_link_to_workspace_card(
        WORKSPACE, "Billing Reports", "Report", "RO Sold Hours", is_query_report=1
    )


def add_vehicle_movement_to_workshop():
    """Add the Vehicle Movement page to the Workshop card of the Workshop workspace.

    Re-applied on `after_migrate` for the same reason as `add_ro_sold_hours_to_workshop`.
    """
    add_link_to_workspace_card(
        WORKSPACE, "Workshop", "Page", "vehicle_movement", label="Vehicle Movement"
    )


def add_link_to_workspace_card(
    workspace, card, link_type, link_to, label=None, is_query_report=0
):
    """Append a link to the end of a card in a workspace, if it is not there already."""
    if not frappe.db.exists("Workspace", workspace) or not frappe.db.exists(
        link_type, link_to
    ):
        return

    doc = frappe.get_doc("Workspace", workspace)
    rows = [{field: link.get(field) for field in LINK_FIELDS} for link in doc.links]

    card_idx = next(
        (
            i
            for i, row in enumerate(rows)
            if row["type"] == "Card Break" and row["label"] == card
        ),
        None,
    )
    if card_idx is None:
        return

    link_count = int(rows[card_idx].get("link_count") or 0)
    card_links = rows[card_idx + 1 : card_idx + 1 + link_count]

    if any(row.get("link_to") == link_to for row in card_links):
        return

    rows.insert(
        card_idx + 1 + link_count,
        {
            "type": "Link",
            "label": label or link_to,
            "hidden": 0,
            "link_type": link_type,
            "link_to": link_to,
            "onboard": 0,
            "is_query_report": is_query_report,
            "link_count": 0,
        },
    )
    rows[card_idx]["link_count"] = link_count + 1

    doc.set("links", [])
    for row in rows:
        doc.append("links", row)

    doc.save(ignore_permissions=True)
