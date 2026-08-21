# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import frappe
from automotive.automotive.report.workshop_productivity.workshop_productivity import (
    WorkshopProductivityReport,
)
from frappe.utils.data import flt

from .html_generator_employee_incentive_calculation import (
    generate_ladder_html,
    generate_weightage_table,
    rate_based_generate_ladder_html,
)
from .util_employee_incentive_calculation import (
    get_ladder_result,
    get_rate_ladder_result,
    get_weightage_amount,
)

INCENTIVE_FIELD_MAP = {
    "base_incentive": (0, 0),
    "below_85": (None, 85.0),
    "between_85_and_100": (85.0, 100.0),
    "between_100_and_115": (100.0, 115.0),
    "between_115_and_125": (115.0, 125.0),
    "above_125": (125.0, None),
}

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
        "efficiency_ladder": {85: 0, 125: 85},
        "proficiency_ladder": {85: 0, 125: 85},
        "qc_ro_ladder": {10: 0, 125: 10},
        "cfb_rate_ladder": {4.5: 0, 4.6: 100.0},
    },
}


def execute(filters=None):
    # filters["reporting_manager"] = 28864
    if filters.get("based_on") == "Technician":
        filters["group_by_1"] = "Group by Technician/Bay/Equipment"
    elif filters.get("based_on") == "Reporting Authority":
        filters["group_by_1"] = "Group by Reporting Authority"
        filters["include_tasks"] = 1

    produtivity_report = WorkshopProductivityReport(filters).run()
    columns = produtivity_report[0]
    columns = update_columns(filters, columns)
    data = produtivity_report[1]
    generator = process_rows(filters, data)

    filtered_data = []
    total_data_length = 0
    total_filtered_data_length = 0
    for row in generator:
        total_data_length += 1
        if "_summary" in row:
            continue
        total_filtered_data_length += 1
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

    qc_ro_ladder_html_table = generate_ladder_html(
        filters.get("based_on"), "qc_ro_ladder", "QC RO %"
    )
    cfb_rate_ladder_html_table = rate_based_generate_ladder_html(
        filters.get("based_on"), "cfb_rate_ladder", "QC RO %"
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

            # CFB Rate Ladder
            if cfb_rate_ladder_html_table:
                summary_html += f"""
                    <div style="
                        width: 100%;
                    ">
                        {cfb_rate_ladder_html_table}
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


def validate_efficiency_filter(filters, each_data):
    filter_type = filters.get("efficiency_filter")
    if not filter_type:
        return True

    if not filters.get(filter_type):
        return False

    efficiency = each_data.get("per_efficiency") or 0

    min_val, max_val = INCENTIVE_FIELD_MAP.get(filter_type, (None, None))

    if min_val is not None and efficiency < min_val:
        return False

    if max_val is not None and efficiency >= max_val:
        return False

    return True


def get_efficiency_cap(row_data):
    efficiency = row_data.get("per_efficiency") or 0
    for key, (min_val, max_val) in INCENTIVE_FIELD_MAP.items():
        if min_val is not None and efficiency < min_val:
            continue
        if max_val is not None and efficiency >= max_val:
            continue
        return key
    return None


def compute_incentive(data_row, based_on):
    total_amount = 0
    if BASED_ON_TEMPLATE_DATA.get(based_on):
        weightages = BASED_ON_TEMPLATE_DATA.get(based_on).get("weightages", {})
        field_list = [key + "_amt" for key in weightages]
        for each_field in field_list:
            total_amount += data_row.get(each_field) or 0
        return flt(total_amount, 2)


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
                te.reports_to,
                te.reports_to_name,
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
            join
                tabEmployee te
            on
            	te.name = tt3.assigned_to
            where
                tcf.status = 'Completed'
                and te.reports_to != ""
                and tt.docstatus < 2
                and te.reports_to is not null {condition}
        ) cbf_task_employee
        group by
            cbf_task_employee.reports_to;
    """,
        condition_dict,
        as_dict=True,
    )


def process_rows(filters, data):
    qc_task_types = set(
        frappe.get_all("Task Type", filters={"name": ["like", "%QC%"]}, pluck="name")
    )

    if filters.get("based_on") == "Reporting Authority":
        customer_feed_back = fetch_avg_customer_feed_back_overall(filters) or []
        feedback_map = {d.get("reports_to"): d for d in customer_feed_back}

    efficiency_cap_counts = {}

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
            qc_ro_ladder_result = get_ladder_result(
                based_on=filters.get("based_on"),
                sold_hrs_percentage=totals_dict.get("total_qc_ro_percentage"),
                ladder_field="qc_ro_ladder",
                top_cap=125.0,
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
                if reports_to and reports_to in feedback_map:
                    cfb = feedback_map[reports_to]

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

            if not validate_efficiency_filter(filters, totals_dict):
                continue

            for field in INCENTIVE_FIELD_MAP:
                if filters.get(field):
                    totals_dict[field] = filters.get(field)

            efficiency_cap = get_efficiency_cap(totals_dict)
            efficiency_cap_counts[efficiency_cap] = (
                efficiency_cap_counts.get(efficiency_cap, 0) + 1
            )

            if efficiency_cap:
                totals_dict["calculated_incentive"] = compute_incentive(
                    totals_dict,
                    filters.get("based_on"),
                )

            yield totals_dict

    # return counts separately if needed
    yield {"_summary": efficiency_cap_counts}
