# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from automotive.automotive.report.workshop_productivity.workshop_productivity import (
    WorkshopProductivityReport,
)
from automotive.automotive.report.workshop_turnover.workshop_turnover import (
    WorkshopTurnoverReport,
)
from frappe.utils import getdate
from frappe.utils.data import flt

from .html_generator_employee_incentive_calculation import (
    generate_ladder_html,
    generate_weightage_table,
    rate_based_generate_ladder_html,
)
from .util_employee_incentive_calculation import (
    compute_incentive,
    get_ladder_result,
    get_rate_ladder_result,
    get_weightage_amount,
    service_advisor_process_rows,
)

BASED_ON_TEMPLATE_DATA = {
    "Technician": {
        "weightages": {"sold_hrs": 50, "efficiency": 25, "productivity": 25},
        "sold_hrs_ladder": {
            80: 0,
            85: 80,
            90: 85,
            95: 90,
            100: 95,
            105: 100,
            115: 105,
            125: 115,
        },
        "efficiency_ladder": {
            90: 0,
            95: 90,
            100: 95,
            105: 100,
            110: 105,
            115: 110,
            120: 115,
            125: 120,
        },
        "productivity_ladder": {
            85: 0,
            90: 85,
            95: 90,
            100: 95,
            105: 100,
            110: 105,
            115: 110,
            125: 115,
        },
    },
    "Reporting Authority": {
        "weightages": {
            "efficiency": 30,
            "proficiency": 30,
            "qc_ro": 20,
            "customer_feedback": 20,
        },
        "efficiency_ladder": {
            85: 0,
            90: 85,
            95: 90,
            100: 95,
            105: 100,
            110: 105,
            115: 110,
            125: 115,
        },
        "proficiency_ladder": {
            85: 0,
            90: 85,
            95: 90,
            100: 95,
            105: 100,
            110: 105,
            115: 110,
            125: 115,
        },
        "qc_ro_ladder": {9.9: 0, 10: 100.0},
        "cfb_rate_ladder": {4.5: 0, 4.6: 100.0},
    },
    "Service Advisor": {
        "weightages": {"revenue": 45, "customer_feedback": 35, "wip_ageing": 20},
        "revenue_ladder": {"Target Revenue": 100.0},
        "wip_ageing_ladder": {45: 100.0, 46: 0.0},
        "cfb_rate_ladder": {4.5: 0, 4.6: 100.0},
    },
}


def execute(filters=None):
    workshop_turnover_report_data = []
    data = []
    columns = []
    if filters.get("based_on") == "Technician":
        filters["group_by_1"] = "Group by Technician/Bay/Equipment"
    elif filters.get("based_on") == "Reporting Authority":
        filters["group_by_1"] = "Group by Reporting Authority"
        filters["include_tasks"] = 1
    elif filters.get("based_on") == "Service Advisor":
        filters["group_by_1"] = "Group by Service Advisor"
        filters["include_tasks"] = 1
        workshop_turnover_report = WorkshopTurnoverReport(filters).run()
        workshop_turnover_report_data = workshop_turnover_report[1]
        columns = update_columns(filters, columns)

    # Productivity Report
    if filters.get("based_on") != "Service Advisor":
        produtivity_report = WorkshopProductivityReport(filters).run()
        productivity_columns = produtivity_report[0]
        columns = update_columns(filters, productivity_columns)
        data = produtivity_report[1]
    generator = process_rows(filters, data, workshop_turnover_report_data)

    filtered_data = []
    for row in generator:
        if "_summary" in row:
            continue
        filtered_data.append(row)

    summary_html = ""
    based_on_html_table = generate_weightage_table(
        filters.get("based_on"),
        filters.get("base_incentive"),
    )

    sold_hrs_ladder_html_table = generate_ladder_html(
        filters.get("based_on"), "sold_hrs_ladder", "Sold Hrs %"
    )

    efficiency_ladder_html_table = generate_ladder_html(
        filters.get("based_on"), "efficiency_ladder", "Efficiency %"
    )

    productivity_ladder_html_table = generate_ladder_html(
        filters.get("based_on"), "productivity_ladder", "Productivity %"
    )

    proficiency_ladder_html_table = generate_ladder_html(
        filters.get("based_on"), "proficiency_ladder", "Proficiency %"
    )

    qc_ro_ladder_html_table = rate_based_generate_ladder_html(
        filters.get("based_on"), "qc_ro_ladder", "QC RO", "%"
    )

    revenue_ladder_html_table = rate_based_generate_ladder_html(
        filters.get("based_on"), "revenue_ladder", "Revenue"
    )

    cfb_rate_ladder_html_table = rate_based_generate_ladder_html(
        filters.get("based_on"), "cfb_rate_ladder", "Customer Feedback Rate"
    )

    wip_ageing_ladder_html_table = rate_based_generate_ladder_html(
        filters.get("based_on"), "wip_ageing_ladder", "Average WIP Ageing"
    )

    summary_html = ""

    if (
        based_on_html_table
        or sold_hrs_ladder_html_table
        or efficiency_ladder_html_table
        or productivity_ladder_html_table
        or proficiency_ladder_html_table
        or qc_ro_ladder_html_table
        or cfb_rate_ladder_html_table
        or wip_ageing_ladder_html_table
        or revenue_ladder_html_table
    ):
        summary_html = """
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
        ">
            <tr>
        """

        # Left side - Weightage table
        if based_on_html_table:
            summary_html += f"""
                <td style="
                    width: 25%;
                    vertical-align: top;
                    padding: 5px;
                ">
                    {based_on_html_table}
                </td>
            """

        # Right side - Ladder tables
        if (
            sold_hrs_ladder_html_table
            or efficiency_ladder_html_table
            or productivity_ladder_html_table
            or proficiency_ladder_html_table
            or qc_ro_ladder_html_table
            or cfb_rate_ladder_html_table
            or wip_ageing_ladder_html_table
            or revenue_ladder_html_table
        ):
            summary_html += """
                <td style="
                    width: 75%;
                    vertical-align: top;
                    padding: 5px;
                ">
            """

            # Sold Hrs Ladder
            if sold_hrs_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {sold_hrs_ladder_html_table}
                    </div>
                """

            # Efficiency Ladder
            if efficiency_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {efficiency_ladder_html_table}
                    </div>
                """

            # Productivity Ladder
            if productivity_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                    ">
                        {productivity_ladder_html_table}
                    </div>
                """

            # Prficiency Ladder
            if proficiency_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {proficiency_ladder_html_table}
                    </div>
                """

            # QC RO Ladder
            if qc_ro_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {qc_ro_ladder_html_table}
                    </div>
                """
            # revenue_ladder_html_table
            # Revenue Ladder
            if revenue_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {revenue_ladder_html_table}
                    </div>
                """

            # CFB Rate Ladder
            if cfb_rate_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {cfb_rate_ladder_html_table}
                    </div>
                """

            # CFB Rate Ladder
            if wip_ageing_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                    ">
                        {wip_ageing_ladder_html_table}
                    </div>
                """

            summary_html += """
                </td>
            """

        summary_html += """
            </tr>
        </table>
        """

    return (
        columns,
        filtered_data,
        summary_html,
        None,
        None,
    )


def update_columns(filters, columns):
    for each_column in columns:
        if each_column.get("fieldname") in [
            "mttr",
            "no_of_repair_orders",
            "per_utilization",
            "reference",
            "vehicle_workshop",
            "vehicle_workshop_division",
            "employee",
            "employee_name",
            "technician_workshop_division",
            "vehicle_service_bay",
            "vehicle_service_bay_title",
            "project",
            "task",
            "task_type",
            "subject",
            "reports_to",
            "reports_to_name",
            "service_advisor",
        ]:
            each_column["hidden"] = 1

    employee_columns = []

    based_on = filters.get("based_on")

    columns_map = {
        "Technician": [
            {
                "label": "Employee ID",
                "fieldname": "employee",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
            {
                "label": "Employee Name",
                "fieldname": "employee_name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": "Reporting Manger",
                "fieldname": "reports_to",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
        ],
        "Reporting Authority": [
            {
                "label": "Reporting Manger",
                "fieldname": "reports_to",
                "fieldtype": "Link",
                "options": "Employee",
                "width": 150,
            },
            {
                "label": "Reporting Manger Name",
                "fieldname": "reports_to_name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": "Avg. CFB",
                "fieldname": "customer_overall_rating",
                "fieldtype": "Rating",
                "width": 200,
            },
            {
                "label": "Rating Value",
                "fieldname": "customer_overall_rating_value",
                "fieldtype": "Float",
                "width": 150,
                "hidden": 1,
            },
            {
                "label": "RO Count (CFB)",
                "fieldname": "ro_count_cfb",
                "fieldtype": "Int",
                "width": 150,
            },
            {
                "label": "QC RO Count",
                "fieldname": "total_qc_ro_count",
                "fieldtype": "Int",
                "width": 150,
            },
            {
                "label": "Non QC RO Count",
                "fieldname": "total_ro_count_non_qc",
                "fieldtype": "Int",
                "width": 150,
            },
        ],
        "Service Advisor": [
            {
                "label": frappe._("Service Advisor"),
                "fieldname": "service_advisor",
                "fieldtype": "Link",
                "options": "Sales Person",
                "width": 150,
            },
            {
                "label": "Avg. CFB",
                "fieldname": "customer_overall_rating",
                "fieldtype": "Rating",
                "width": 200,
            },
            {
                "label": "Sales Amount",
                "fieldname": "total_sales_amount",
                "fieldtype": "Currency",
                "width": 100,
            },
            {
                "label": "Target Revenue",
                "fieldname": "sa_target_revenue",
                "fieldtype": "Currency",
                "width": 100,
            },
            {
                "label": "WIP RO Count",
                "fieldname": "wip_ro_count",
                "fieldtype": "Int",
                "width": 100,
            },
            {
                "label": "WIP Average Age",
                "fieldname": "wip_average_age",
                "fieldtype": "Float",
                "width": 100,
            },
        ],
    }

    employee_columns = columns_map.get(based_on, [])

    columns[:0] = employee_columns

    incentive_columns = []
    if BASED_ON_TEMPLATE_DATA.get(based_on):
        if BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages"):
            incentive_columns = [
                {
                    "label": format_label(field) + " Amt",
                    "fieldname": field + "_amt",
                    "fieldtype": "Float",
                    "width": 150,
                }
                for field in BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages")
            ]

    if based_on in ["Reporting Authority", "Technician"]:
        columns.extend(
            [
                {
                    "label": "Sold Hrs. %",
                    "fieldname": "sold_hrs_percentage",
                    "fieldtype": "Float",
                    "width": 100,
                }
            ]
        )

    if based_on == "Reporting Authority":
        columns.extend(
            [
                {
                    "label": "QC RO %",
                    "fieldname": "total_qc_ro_percentage",
                    "fieldtype": "Float",
                    "width": 100,
                }
            ]
        )

    if incentive_columns:
        columns.extend(incentive_columns)

    columns.append(
        {
            "label": "Calculated Incentive",
            "fieldname": "calculated_incentive",
            "fieldtype": "Currency",
            "width": 150,
        }
    )
    return columns


def format_label(fieldname):
    if fieldname == "base_incentive":
        return "Base Incentive"

    parts = fieldname.split("_")

    if parts[0] == "below":
        return f"Below {parts[1]}%"

    if parts[0] == "between":
        return f"Between {parts[1]} and {parts[3]}"

    return fieldname.replace("_", " ").title()


def fetch_avg_customer_feed_back_overall(filters):
    condition_dict = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
    }

    condition = "and %(from_dt)s <= ttd.to_time and %(to_dt)s >= ttd.from_time"

    return frappe.db.sql(
        f"""
        select
            cbf_task_employee.reports_to,
            cbf_task_employee.reports_to_name,
            count(distinct cbf_task_employee.project) as ro_count,
            round(avg(cbf_task_employee.overall_satisfaction_rating), 2) as avg_rating
        from (
            select distinct
                tt3.reports_to,
                tt3.reports_to_name,
                tt3.project,
                tcf.overall_satisfaction_rating
            from
                `tabTimesheet Detail` ttd
            join
            	tabTimesheet tt
            on
            	tt.name = ttd.parent
            join
            	tabTask tt3
            on
            	tt3.name = ttd.task
            join
                `tabCustomer Feedback` tcf
            on
            	tt3.project = tcf.project
            where
                tcf.status = 'Completed'
                and tt3.reports_to != ""
                and tt.docstatus < 2
                and tt3.reports_to is not null {condition}
        ) cbf_task_employee
        group by
            cbf_task_employee.reports_to;
    """,
        condition_dict,
        as_dict=True,
    )


def fetch_avg_customer_feed_back_overall_service_advisor(filters):
    condition_dict = {
        "from_dt": filters.get("from_date"),
        "to_dt": filters.get("to_date"),
    }

    return frappe.db.sql(
        """
        select
            cbf_task_sa.service_advisor,
            count(distinct cbf_task_sa.project) as ro_count,
            round(avg(cbf_task_sa.overall_satisfaction_rating), 2) as avg_rating
        from (
            select distinct
                p.service_advisor,
                p.name as project,
                tcf.overall_satisfaction_rating
            from
                `tabSales Invoice` si
            join
                `tabSales Invoice Item` sii
            on
                sii.parent = si.name
            join
                `tabProject` p
            on
                p.name = sii.project
            join
                `tabCustomer Feedback` tcf
            on
                p.name = tcf.project
            where
                tcf.status = 'Completed'
                and p.service_advisor != ""
                and p.service_advisor is not null
                and si.docstatus = 1
                and si.posting_date between %(from_dt)s and %(to_dt)s
                and sii.project is not null
                and sii.project != ""
        ) cbf_task_sa
        group by
            cbf_task_sa.service_advisor;
    """,
        condition_dict,
        as_dict=True,
    )


def fetch_target_sa(filters):
    to_date = getdate(filters.get("to_date") or getdate())
    year = to_date.year
    month_field = to_date.strftime("%B").lower()

    rows = frappe.db.sql(
        f"""
        select
            td.service_advisor,
            td.{month_field} as target_amount
        from
            `tabTarget Details` td
        where
            td.parent = 'Target Settings'
            and td.parenttype = 'Target Settings'
            and td.parentfield = 'service_advisor_targets'
            and td.year = %(year)s
            and td.service_advisor is not null
            and td.service_advisor != ''
        """,
        {"year": year},
        as_dict=True,
    )

    return {row.get("service_advisor"): flt(row.get("target_amount")) for row in rows}


def fetch_wip_average_age_service_advisor(filters):
    as_of = getdate(filters.get("to_date") or getdate())

    return frappe.db.sql(
        """
        select
            p.service_advisor,
            count(p.name) as ro_count,
            round(avg(datediff(%(as_of)s, date(p.project_date))), 2) as average_wip_age
        from
            `tabProject` p
        where
            p.status != 'Cancelled'
            and p.project_status != 'Completed'
            and p.service_advisor is not null
            and p.service_advisor != ''
            and p.project_date <= %(as_of)s
        group by
            p.service_advisor;
        """,
        {"as_of": as_of},
        as_dict=True,
    )


def process_rows(filters, data, workshop_turnover_report_data=None):
    qc_task_types = set(
        frappe.get_all("Task Type", filters={"name": ["like", "%QC%"]}, pluck="name")
    )

    if filters.get("based_on") == "Reporting Authority":
        customer_feed_back = fetch_avg_customer_feed_back_overall(filters) or []
        reporting_authority_feedback_map = {
            d.get("reports_to"): d for d in customer_feed_back
        }

    if filters.get("based_on") == "Service Advisor":
        customer_feed_back = (
            fetch_avg_customer_feed_back_overall_service_advisor(filters) or []
        )
        service_advisor_feedback_map = {
            d.get("service_advisor"): d for d in customer_feed_back
        }
        wip_average_age_sa = fetch_wip_average_age_service_advisor(filters) or []
        target_sa = fetch_target_sa(filters)

        if workshop_turnover_report_data:
            yield from service_advisor_process_rows(
                filters,
                workshop_turnover_report_data,
                service_advisor_feedback_map,
                wip_average_age_sa,
                target_sa,
            )

    for each_data in data:
        # calculate sold_hours_percentage
        if each_data.get("sold_time") and each_data.get("available_hours"):
            each_data["sold_hrs_percentage"] = flt(
                (each_data.get("sold_time") / each_data.get("available_hours")) * 100.0,
                3,
            )
        else:
            each_data["sold_hrs_percentage"] = 0.0

        for each_group_rows in each_data.rows:
            totals_dict = each_group_rows.totals or {}

            ro_set, qc_ro_set = set(), set()

            for row in each_group_rows.rows or []:
                if row.get("task_type") in qc_task_types:
                    qc_ro_set.add(row.get("project"))
                else:
                    ro_set.add(row.get("project"))

            # Sold Hours Section
            if totals_dict.get("sold_time") and totals_dict.get("available_hours"):
                totals_dict["sold_hrs_percentage"] = flt(
                    (totals_dict.get("sold_time") / totals_dict.get("available_hours"))
                    * 100.0,
                    3,
                )
            else:
                totals_dict["sold_hrs_percentage"] = 0.0

            sold_hrs_ladder_result = get_ladder_result(
                based_on=filters.get("based_on"),
                sold_hrs_percentage=totals_dict.get("sold_hrs_percentage"),
                ladder_field="sold_hrs_ladder",
                top_cap=125.0,
            )

            if sold_hrs_ladder_result:
                sold_hrs_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="sold_hrs",
                    )
                    or 0
                )
                totals_dict["sold_hrs_amt"] = flt(
                    sold_hrs_weightage_amount * (sold_hrs_ladder_result / 100.0), 3
                )
            else:
                totals_dict["sold_hrs_amt"] = 0

            # Efficiency Section
            efficiency_ladder_result = get_ladder_result(
                based_on=filters.get("based_on"),
                sold_hrs_percentage=totals_dict.get("per_efficiency"),
                ladder_field="efficiency_ladder",
                top_cap=125.0,
            )
            if efficiency_ladder_result:
                efficiency_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="efficiency",
                    )
                    or 0
                )
                totals_dict["efficiency_amt"] = flt(
                    efficiency_weightage_amount * (efficiency_ladder_result / 100.0), 3
                )
            else:
                totals_dict["efficiency_amt"] = 0

            # Productivity Section
            productivity_ladder_result = get_ladder_result(
                based_on=filters.get("based_on"),
                sold_hrs_percentage=totals_dict.get("per_productivity"),
                ladder_field="productivity_ladder",
                top_cap=125.0,
            )
            if productivity_ladder_result:
                productivity_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="productivity",
                    )
                    or 0
                )
                totals_dict["productivity_amt"] = flt(
                    productivity_weightage_amount
                    * (productivity_ladder_result / 100.0),
                    3,
                )
            else:
                totals_dict["productivity_amt"] = 0

            # Proficiency Section
            proficiency_ladder_result = get_ladder_result(
                based_on=filters.get("based_on"),
                sold_hrs_percentage=totals_dict.get("per_proficiency"),
                ladder_field="proficiency_ladder",
                top_cap=125.0,
            )
            if proficiency_ladder_result:
                proficiency_weightage_amount = (
                    get_weightage_amount(
                        based_on=filters.get("based_on"),
                        base_incentive=filters.get("base_incentive"),
                        field_name="proficiency",
                    )
                    or 0
                )
                totals_dict["proficiency_amt"] = flt(
                    proficiency_weightage_amount * (proficiency_ladder_result / 100.0),
                    3,
                )
            else:
                totals_dict["proficiency_amt"] = 0

            totals_dict["total_ro_count_non_qc"] = len(ro_set)
            totals_dict["total_qc_ro_count"] = len(qc_ro_set)
            totals_dict["total_qc_ro_percentage"] = flt(
                (len(qc_ro_set) / (len(ro_set) + len(qc_ro_set))) * 100.0, 3
            )

            # QC_RO Section
            qc_ro_ladder_result = get_rate_ladder_result(
                based_on=filters.get("based_on"),
                percentage=totals_dict.get("total_qc_ro_percentage"),
                ladder_field="qc_ro_ladder",
                top_cap=10.0,
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
                    qc_ro_weightage_amount * (qc_ro_ladder_result / 100.0), 3
                )
            else:
                totals_dict["qc_ro_amt"] = 0

            if totals_dict.get("_bold"):
                totals_dict["_bold"] = 0

            if filters.get("based_on") == "Reporting Authority":
                totals_dict["customer_feedback_amt"] = 0
                reports_to = totals_dict.get("reports_to")
                if reports_to and reports_to in reporting_authority_feedback_map:
                    cfb = reporting_authority_feedback_map[reports_to]

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
                        else:
                            totals_dict["customer_feedback_amt"] = 0

            # filtering
            if filters.get("based_on") == "Reporting Authority":
                if not totals_dict.get("reports_to"):
                    continue

            totals_dict["calculated_incentive"] = compute_incentive(
                totals_dict,
                filters.get("based_on"),
            )

            yield totals_dict
