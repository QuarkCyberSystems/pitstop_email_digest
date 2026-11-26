import frappe
from frappe.utils import get_datetime, now_datetime

# Project.status values after which the clock stops
FINAL_STATUSES = ("Completed", "Closed", "Cancelled")


@frappe.whitelist()
def get_status_train(project):
    """Return the Repair Order's job status journey from Draft onwards.

    Every change of Project.project_status is logged as a "Label" comment
    (see Project.set_status), so the journey is rebuilt from those comments.
    A status that is visited more than once (e.g. To Assign -> Assigned ->
    In Progress loops) becomes a single stop with its time summed up.
    """
    doc = frappe.get_doc("Project", project)
    doc.check_permission("read")

    changes = frappe.get_all(
        "Comment",
        filters={
            "reference_doctype": "Project",
            "reference_name": project,
            "comment_type": "Label",
        },
        fields=["content", "creation"],
        order_by="creation asc",
    )

    is_final = doc.status in FINAL_STATUSES
    current_status = doc.project_status or doc.status

    # (status, start) in chronological order, starting with Draft at creation
    timeline = [("Draft", get_datetime(doc.creation))]
    for change in changes:
        status = frappe.utils.strip_html(change.content or "").strip()
        if status and status != timeline[-1][0]:
            timeline.append((status, get_datetime(change.creation)))

    stops = {}
    for i, (status, start) in enumerate(timeline):
        is_last = i == len(timeline) - 1
        if is_last:
            end = None if is_final else now_datetime()
        else:
            end = timeline[i + 1][1]

        stop = stops.setdefault(
            status,
            frappe._dict(status=status, start=start, seconds=0, visits=0),
        )
        stop.visits += 1
        if end:
            stop.seconds += max((end - start).total_seconds(), 0)

    end_of_journey = timeline[-1][1] if is_final else now_datetime()

    return {
        "stops": list(stops.values()),
        "current_status": current_status,
        "is_final": is_final,
        "total_seconds": max((end_of_journey - timeline[0][1]).total_seconds(), 0),
    }
