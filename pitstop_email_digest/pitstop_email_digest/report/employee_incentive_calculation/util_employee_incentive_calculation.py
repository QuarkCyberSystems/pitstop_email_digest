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
    allowed_service_advisors=None,
):
    for each_turnover_data in workshop_turnover_report_data:
        for each_group_data in each_turnover_data.rows:
            totals_dict = each_group_data.totals
            if not totals_dict.get("service_advisor"):
                continue
            if (
                allowed_service_advisors is not None
                and totals_dict.get("service_advisor") not in allowed_service_advisors
            ):
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

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            yield totals_dict


def quality_control_process_rows(
    filters,
    data,
    quality_controller_feedback_map,
    qc_task_types,
    qc_technicians=None,
):
    for each_data in data:
        if not each_data.get("rows"):
            continue

        for each_group_rows in each_data.rows:
            totals_dict = each_group_rows.totals or {}

            if qc_technicians:
                assignee = each_group_rows.get("employee") or totals_dict.get(
                    "employee"
                )
                if assignee not in qc_technicians:
                    continue
                totals_dict["customer_feedback_amt"] = 0.0
                if assignee and assignee in quality_controller_feedback_map:
                    cfb = quality_controller_feedback_map[assignee]

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

            all_ro = set()
            ro_with_qc = set()
            qc_invoice_ro = set()
            comeback_ro = set()

            for row in each_group_rows.rows or []:
                repair_order = row.get("project")
                if not repair_order:
                    continue

                all_ro.add(repair_order)

                if row.get("task_type") in qc_task_types:
                    ro_with_qc.add(repair_order)

                if (
                    (row.get("task_type") in qc_task_types)
                    and flt(row.get("billed_amount"))
                ) > 0:
                    qc_invoice_ro.add(repair_order)

                if row.get("service_type") == "Comeback":
                    comeback_ro.add(repair_order)

            qc_projects = ro_with_qc
            non_qc_projects = all_ro - ro_with_qc

            total_ro = len(all_ro)
            total_qc_ro = len(qc_projects)
            total_comeback_ro = len(comeback_ro)
            totals_dict["total_qc_ro_count"] = total_qc_ro
            totals_dict["total_ro_count_non_qc"] = len(non_qc_projects)
            totals_dict["total_qc_invoice_ro_count"] = len(qc_invoice_ro)
            totals_dict["total_comeback_ro_count"] = len(comeback_ro)
            totals_dict["total_ro_count"] = total_ro

            # Invoiced RO% QC Invoiced
            totals_dict["qc_ro_amt"] = 0.0
            percentage_of_invoiced_qc_ro = (
                flt((len(qc_invoice_ro) / total_qc_ro) * 100, 3) if total_qc_ro else 0.0
            )

            qc_ro_ladder_result = get_rate_ladder_result(
                based_on=filters.get("based_on"),
                percentage=percentage_of_invoiced_qc_ro,
                ladder_field="qc_ro_ladder",
                top_cap=5.0,
            )

            if qc_ro_ladder_result:
                qc_ro_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="qc_ro",
                    )
                    or 0
                )
                totals_dict["qc_ro_amt"] = flt(
                    qc_ro_weightage_amount * (qc_ro_ladder_result / 100.0),
                    3,
                )

            # Comeback RO% From Total RO
            totals_dict["come_back_ro_amt"] = 0.0
            percentage_of_comeback_ro = (
                flt((total_comeback_ro / total_ro) * 100, 3) if total_ro else 0.0
            )

            come_back_ro_ladder_result = get_rate_ladder_result(
                based_on=filters.get("based_on"),
                percentage=percentage_of_comeback_ro,
                ladder_field="come_back_ro_ladder",
                top_cap=5.0,
            )

            if come_back_ro_ladder_result:
                come_back_ro_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="come_back_ro",
                    )
                    or 0
                )
                totals_dict["come_back_ro_amt"] = flt(
                    come_back_ro_weightage_amount
                    * (come_back_ro_ladder_result / 100.0),
                    3,
                )

            totals_dict["total_qc_ro_percentage"] = (
                flt((len(qc_projects) / total_ro) * 100.0, 3) if total_ro else 0.0
            )

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            totals_dict["calculated_incentive"] = compute_incentive(
                totals_dict,
                filters.get("based_on"),
            )

            yield totals_dict
