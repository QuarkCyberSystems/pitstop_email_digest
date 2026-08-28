from frappe.utils import flt


def get_ladder_result(based_on, sold_hrs_percentage, ladder_field, top_cap):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if BASED_ON_TEMPLATE_DATA.get(based_on):
        ladder = BASED_ON_TEMPLATE_DATA.get(based_on).get(ladder_field)

        if ladder:
            for threshold, result in ladder.items():
                if sold_hrs_percentage < threshold:
                    return result
            return top_cap


def get_weightage_amount(based_on, base_incentive, field_name):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    if BASED_ON_TEMPLATE_DATA.get(based_on):
        weightages = BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages", {})

        for key, percentage in weightages.items():
            amount = base_incentive * percentage / 100
            if field_name == key:
                return amount


def get_rate_ladder_result(based_on, percentage, ladder_field, top_cap):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    ladder = BASED_ON_TEMPLATE_DATA.get(based_on, {}).get(ladder_field, {})

    if not ladder:
        return None

    thresholds = sorted(ladder.keys())

    for threshold in reversed(thresholds):
        if percentage >= threshold:
            return ladder[threshold]

    # Less than the lowest threshold
    return ladder[thresholds[0]]


def compute_incentive(data_row, based_on):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    total_amount = 0
    if BASED_ON_TEMPLATE_DATA.get(based_on):
        weightages = BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages", {})
        field_list = [key + "_amt" for key in weightages]
        for each_field in field_list:
            total_amount += data_row.get(each_field) or 0
        return flt(total_amount, 2)


def service_advisor_process_rows(
    filters,
    workshop_turnover_report_data,
    service_advisor_feedback_map,
    wip_average_age_sa,
    target_sa,
):
    for each_turnover_data in workshop_turnover_report_data:
        for each_group_data in each_turnover_data.rows:
            totals_dict = each_group_data.totals
            if not totals_dict.get("service_advisor"):
                continue
            totals_dict["customer_feedback_amt"] = 0.0
            totals_dict["wip_ageing_amt"] = 0.0
            service_advisor = totals_dict.get("service_advisor")
            if service_advisor and service_advisor in service_advisor_feedback_map:
                cfb = service_advisor_feedback_map[service_advisor]

                if cfb.get("avg_rating"):
                    rating = flt(cfb.get("avg_rating"), 2)
                    totals_dict["customer_overall_rating"] = rating
                    totals_dict["customer_overall_rating_value"] = rating
                    rating_out_of_five = flt((rating / 2) * 10.0, 2)
                    totals_dict["ro_count_cfb"] = cfb.get("ro_count")

                    # CFB Section cfb_rate_ladder
                    cfb_rate_ladder_result = get_rate_ladder_result(
                        based_on=filters.get("based_on"),
                        percentage=rating_out_of_five,
                        ladder_field="cfb_rate_ladder",
                        top_cap=5.0,
                    )
                    if cfb_rate_ladder_result:
                        customer_feedback_weightage_amount = (
                            get_weightage_amount(
                                based_on=filters.get("based_on"),
                                base_incentive=filters.get("base_incentive"),
                                field_name="customer_feedback",
                            )
                            or 0
                        )
                        totals_dict["customer_feedback_amt"] = flt(
                            customer_feedback_weightage_amount
                            * (cfb_rate_ladder_result / 100.0),
                            3,
                        )
            for each_service_advisor_wip_average_age in wip_average_age_sa:
                if (
                    each_service_advisor_wip_average_age.get("service_advisor")
                    == service_advisor
                ):
                    totals_dict["wip_average_age"] = flt(
                        each_service_advisor_wip_average_age.get("average_wip_age")
                    )
                    totals_dict["wip_ro_count"] = flt(
                        each_service_advisor_wip_average_age.get("ro_count")
                    )
                    if flt(totals_dict["wip_average_age"]) <= 46.0:
                        wip_average_age_weightage_amount = (
                            get_weightage_amount(
                                based_on=filters.get("based_on"),
                                base_incentive=filters.get("base_incentive"),
                                field_name="wip_ageing",
                            )
                            or 0
                        )
                        totals_dict["wip_ageing_amt"] = flt(
                            wip_average_age_weightage_amount,
                            3,
                        )
                        break
            else:
                totals_dict["wip_ro_count"] = 0
                totals_dict["wip_average_age"] = 0.0
                wip_average_age_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="wip_ageing",
                    )
                    or 0
                )
                totals_dict["wip_ageing_amt"] = flt(
                    wip_average_age_weightage_amount,
                    3,
                )
            if service_advisor and service_advisor in target_sa:
                totals_dict["sa_target_revenue"] = target_sa[service_advisor]
            else:
                totals_dict["sa_target_revenue"] = 0.0

            # Revenue section
            if flt(totals_dict.get("sa_target_revenue")) <= flt(
                totals_dict.get("total_sales_amount")
            ):
                revenue_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="revenue",
                    )
                    or 0
                )
                totals_dict["revenue_amt"] = flt(
                    revenue_weightage_amount,
                    3,
                )
            else:
                totals_dict["revenue_amt"] = 0.0

            totals_dict["calculated_incentive"] = compute_incentive(
                totals_dict,
                filters.get("based_on"),
            )

            yield totals_dict
