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
    branch_dict = {
        row.get("branch"): {
            "feedback_count": 0,
            "customer_respond_count": 0,
            "customer_satisfaction_index": 0,
            "satisfied_count": 0,
            "neutral_count": 0,
            "dissatisfied_count": 0,
        }
        for row in customer_feed_back_data
        if row.get("branch")
    }

    for row in customer_feed_back_data:
        branch = row.get("branch")

        if branch:
            branch_dict[branch]["feedback_count"] += 1
            if (feedback_status := row.get("feedback_status")) != "Not Reachable":
                branch_dict[branch]["customer_respond_count"] += 1
            if not branch_dict[branch]["customer_satisfaction_index"]:
                customer_satisfaction_index_per = get_rating_percentage(
                    customer_feed_back_data, branch
                )
                branch_dict[branch]["customer_satisfaction_index"] = floor(
                    customer_satisfaction_index_per
                )
            if (feedback_status := row.get("feedback_status")) == "Satisfied":
                branch_dict[branch]["satisfied_count"] += 1
            if (feedback_status := row.get("feedback_status")) == "Neutral":
                branch_dict[branch]["neutral_count"] += 1
            if (feedback_status := row.get("feedback_status")) == "Dissatisfied":
                branch_dict[branch]["dissatisfied_count"] += 1

    return branch_dict


def get_rating_percentage(customer_feed_back_data, branch):
    for fieldname in ["timeliness_rating"]:
        fieldname = fieldname
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
