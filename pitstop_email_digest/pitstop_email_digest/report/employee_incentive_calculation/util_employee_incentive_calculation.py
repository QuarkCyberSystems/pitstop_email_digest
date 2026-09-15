"""Shared incentive primitives.

Everything here is designation agnostic: ladder lookups, weightage maths and
the per-group computation common to the designations driven by the Workshop
Productivity report. Designation specific logic lives in the sibling
``util_<designation>.py`` modules.
"""

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


def get_target_ladder_result(based_on, value, ladder_field, target_value=None):
    """Pass/fail against a target: 0 below it, the ladder's result at or above
    it. `target_value` overrides the target configured on the ladder, for
    targets that come from data rather than the template."""
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    ladder = BASED_ON_TEMPLATE_DATA.get(based_on, {}).get(ladder_field, {})

    if not ladder:
        return None

    if target_value is None:
        target_value = ladder.get("target_value")

    achieved_result = max(
        (
            result
            for key, result in ladder.items()
            if isinstance(key, (int, float)) and not isinstance(key, bool)
        ),
        default=100.0,
    )

    return achieved_result if flt(value) >= flt(target_value) else 0.0


def compute_incentive(data_row, based_on):
    from .employee_incentive_calculation import BASED_ON_TEMPLATE_DATA

    total_amount = 0
    if BASED_ON_TEMPLATE_DATA.get(based_on):
        weightages = BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages", {})
        field_list = [key + "_amt" for key in weightages]
        for each_field in field_list:
            total_amount += data_row.get(each_field) or 0
        return flt(total_amount, 2)


def weightage_amount(filters, field_name):
    return (
        get_weightage_amount(
            based_on=filters.get("based_on"),
            base_incentive=filters.get("base_incentive") or 0.0,
            field_name=field_name,
        )
        or 0
    )


def compute_sold_hrs_amount(filters, totals):
    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=totals.get("sold_hrs_percentage"),
        ladder_field="sold_hrs_ladder",
        top_cap=125.0,
    )
    if result:
        totals["sold_hrs_amt"] = flt(
            weightage_amount(filters, "sold_hrs") * (result / 100.0), 3
        )
    else:
        totals["sold_hrs_amt"] = 0


def compute_efficiency_amount(filters, totals):
    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=totals.get("per_efficiency"),
        ladder_field="efficiency_ladder",
        top_cap=125.0,
    )
    if result:
        totals["efficiency_amt"] = flt(
            weightage_amount(filters, "efficiency") * (result / 100.0), 3
        )
    else:
        totals["efficiency_amt"] = 0


def compute_productivity_amount(filters, totals):
    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=totals.get("per_productivity"),
        ladder_field="productivity_ladder",
        top_cap=125.0,
    )
    if result:
        totals["productivity_amt"] = flt(
            weightage_amount(filters, "productivity") * (result / 100.0), 3
        )
    else:
        totals["productivity_amt"] = 0


def compute_proficiency_amount(filters, totals):
    result = get_ladder_result(
        based_on=filters.get("based_on"),
        sold_hrs_percentage=totals.get("per_proficiency"),
        ladder_field="proficiency_ladder",
        top_cap=125.0,
    )
    if result:
        totals["proficiency_amt"] = flt(
            weightage_amount(filters, "proficiency") * (result / 100.0), 3
        )
    else:
        totals["proficiency_amt"] = 0


def compute_qc_ro_amount(filters, totals):
    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=totals.get("total_qc_ro_percentage"),
        ladder_field="qc_ro_ladder",
        top_cap=10.0,
    )
    if result:
        totals["qc_ro_amt"] = flt(
            weightage_amount(filters, "qc_ro") * (result / 100.0), 3
        )
    else:
        totals["qc_ro_amt"] = 0


def apply_customer_feedback(filters, totals, cfb):
    """Rate the average customer feedback against `cfb_rate_ladder`.

    Shared by every designation carrying a customer feedback weightage:
    Reporting Authority, Service Advisor and Quality Controller.
    """
    totals["customer_feedback_amt"] = 0.0

    if not cfb or not cfb.get("avg_rating"):
        return

    rating = flt(cfb.get("avg_rating"), 2)
    totals["customer_overall_rating"] = rating
    totals["customer_overall_rating_value"] = rating
    rating_out_of_five = flt((rating / 2) * 10.0, 2)
    totals["ro_count_cfb"] = cfb.get("ro_count")

    result = get_rate_ladder_result(
        based_on=filters.get("based_on"),
        percentage=rating_out_of_five,
        ladder_field="cfb_rate_ladder",
        top_cap=5.0,
    )

    if result:
        totals["customer_feedback_amt"] = flt(
            weightage_amount(filters, "customer_feedback") * (result / 100.0), 3
        )


def apply_wip_ageing(filters, totals, wip_average_age_rows, employee_field):
    """Set the WIP ageing figures and amount from `wip_average_age_rows`.

    Shared by Service Advisor and Job Controller, which differ only in the
    field the rows are keyed by.
    """
    employee = totals.get(employee_field)
    totals["wip_ageing_amt"] = 0.0
    totals["wip_ro_count"] = 0

    for each_wip_average_age in wip_average_age_rows:
        if each_wip_average_age.get(employee_field) == employee:
            totals["wip_average_age"] = flt(each_wip_average_age.get("average_wip_age"))
            totals["wip_ro_count"] = flt(each_wip_average_age.get("ro_count"))
            if flt(totals["wip_average_age"]) <= 46.0:
                totals["wip_ageing_amt"] = flt(
                    weightage_amount(filters, "wip_ageing"), 3
                )
                break
    else:
        # No matching row: fall back to a zero age, which still earns the full
        # WIP ageing weightage.
        totals["wip_ro_count"] = 0
        totals["wip_average_age"] = 0.0
        totals["wip_ageing_amt"] = flt(weightage_amount(filters, "wip_ageing"), 3)


def iter_productivity_groups(filters, source_data, qc_task_types):
    """Yield each group's totals for the designations driven by the Workshop
    Productivity report (Technician, Reporting Authority, Job Controller).

    The shared sold hrs / efficiency / productivity / proficiency / QC RO
    figures are already applied; callers layer their own fields on top and
    decide which rows to keep.
    """
    for each_data in source_data:
        if each_data.get("sold_time") and each_data.get("available_hours"):
            each_data["sold_hrs_percentage"] = flt(
                (each_data.get("sold_time") / each_data.get("available_hours")) * 100.0,
                3,
            )
        else:
            each_data["sold_hrs_percentage"] = 0.0

        if not each_data.rows:
            continue

        for each_group_rows in each_data.rows:
            totals_dict = each_group_rows.totals or {}

            ro_set, qc_ro_set = set(), set()
            for row in each_group_rows.rows or []:
                if row.get("task_type") in qc_task_types:
                    qc_ro_set.add(row.get("project"))
                else:
                    ro_set.add(row.get("project"))

            if totals_dict.get("sold_time") and totals_dict.get("available_hours"):
                totals_dict["sold_hrs_percentage"] = flt(
                    (totals_dict.get("sold_time") / totals_dict.get("available_hours"))
                    * 100.0,
                    3,
                )
            else:
                totals_dict["sold_hrs_percentage"] = 0.0

            compute_sold_hrs_amount(filters, totals_dict)
            compute_efficiency_amount(filters, totals_dict)
            compute_productivity_amount(filters, totals_dict)
            compute_proficiency_amount(filters, totals_dict)

            totals_dict["total_ro_count_non_qc"] = len(ro_set)
            totals_dict["total_qc_ro_count"] = len(qc_ro_set)
            totals_dict["total_qc_ro_percentage"] = flt(
                (len(qc_ro_set) / (len(ro_set) + len(qc_ro_set))) * 100.0, 3
            )

            compute_qc_ro_amount(filters, totals_dict)

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            yield totals_dict
