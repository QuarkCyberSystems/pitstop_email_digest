import frappe
from automotive.automotive.report.customer_feedback_index.customer_feedback_index import (
    CustomerFeedbackIndex,
)
from frappe.utils import floor, flt


@frappe.whitelist()
def get_cfb_analysis_data(from_date, to_date):
    customer_feed_back_columns, customer_feed_back_data = CustomerFeedbackIndex(
        frappe._dict({"from_date": from_date, "to_date": to_date})
    ).run()
    branch_dict = process_customer_feed_back(customer_feed_back_data)
    return branch_dict


def process_customer_feed_back(customer_feed_back_data):
    branch_dict = {}

    for row in customer_feed_back_data:
        branch = row.get("branch")
        if not branch:
            continue

        if branch not in branch_dict:
            branch_dict[branch] = {
                "feedback_count": 0,
                "customer_respond_count": 0,
                "customer_satisfaction_index": 0,
                "satisfied_count": 0,
                "neutral_count": 0,
                "dissatisfied_count": 0,
            }

        entry = branch_dict[branch]
        feedback_status = row.get("feedback_status")

        entry["feedback_count"] += 1

        if feedback_status != "Not Reachable":
            entry["customer_respond_count"] += 1

        if feedback_status == "Satisfied":
            entry["satisfied_count"] += 1
        elif feedback_status == "Neutral":
            entry["neutral_count"] += 1
        elif feedback_status == "Dissatisfied":
            entry["dissatisfied_count"] += 1

    # Compute CSI once per branch after all counts are settled
    for branch, entry in branch_dict.items():
        respond = get_rating_percentage(customer_feed_back_data, branch)
        if respond:
            entry["customer_satisfaction_index"] = floor(respond)

    return branch_dict


def get_rating_percentage(customer_feed_back_data, branch):
    fieldname = "timeliness_rating"
    four_above = [
        flt(row.get(fieldname))
        for row in customer_feed_back_data
        if flt(row.get(fieldname)) >= 0.8 and row.get("branch") == branch
    ]
    has_rating = [
        flt(row.get(fieldname))
        for row in customer_feed_back_data
        if flt(row.get(fieldname)) > 0 and row.get("branch") == branch
    ]
    if has_rating:
        score = len(four_above) / len(has_rating)
        percentage = score * 100

    return percentage
