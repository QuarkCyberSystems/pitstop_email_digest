import frappe

# from automotive.automotive.report.customer_feedback_index.customer_feedback_index import (
#     CustomerFeedbackIndex,
# )


@frappe.whitelist()
def get_cfb_analysis_data(from_date, to_date):
    # customer_feed_back_data = CustomerFeedbackIndex(
    #     {"from_date": "2026-05-16", "to_date": "2026-06-16"}
    # ).run()
    pass


def process_customer_feed_back(customer_feed_back_data):
    # branch_list = {
    #     each_branch.get("branch"): [{"feedback_count": 0}]
    #     for each_branch in customer_feed_back_data
    # }
    # for each_feedback_dict in customer_feed_back_data:
    #     pass
    pass
