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

from pitstop_email_digest.pitstop_email_digest.report.key_to_key_report.key_to_key_report import (
    VehicleKeyToKeyReport,
)

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
    "Job Controller": {
        "weightages": {
            "idle_time": 40,
            "productivity": 30,
            "wip_ageing": 20,
            "key_to_key": 10,
        },
        "idle_time_ladder": {14.9: 100.0, 15.0: 0.0},
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
        "wip_ageing_ladder": {44.9: 100.0, 45.0: 0.0},
        "key_to_key_mechanical_ladder": {1.9: 100.0, 2.0: 0.0},
        "key_to_key_bodyshop_ladder": {10.9: 100.0, 11.0: 0.0},
    },
}

HIDDEN_SOURCE_COLUMNS = {
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
}


def execute(filters=None):
    return EmployeeIncentiveCalculationReport(filters).run()


def format_label(fieldname):
    if fieldname == "base_incentive":
        return "Base Incentive"

    parts = fieldname.split("_")

    if parts[0] == "below":
        return f"Below {parts[1]}%"

    if parts[0] == "between":
        return f"Between {parts[1]} and {parts[3]}"

    return fieldname.replace("_", " ").title()


class EmployeeIncentiveCalculationReport:
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.columns = []
        self.data = []
        self.workshop_turnover_report_data = []
        self.qc_task_types = set()
        self.reporting_authority_feedback_map = {}
        self.service_advisor_feedback_map = {}
        self.wip_average_age_sa = []
        self.target_sa = {}
        self.allowed_service_advisors = None

    def run(self):
        self._apply_based_on_filters()
        self._load_source_reports()
        self._prepare_lookups()

        filtered_data = [row for row in self._process_rows() if "_summary" not in row]
        summary_html = self._build_summary_html()

        return (self.columns, filtered_data, summary_html, None, None)

    def _apply_based_on_filters(self):
        based_on = self.filters.get("based_on")
        if based_on == "Technician":
            self.filters["group_by_1"] = "Group by Technician/Bay/Equipment"
        elif based_on == "Reporting Authority":
            self.filters["group_by_1"] = "Group by Reporting Authority"
            self.filters["include_tasks"] = 1
        elif based_on == "Service Advisor":
            self.filters["group_by_1"] = "Group by Service Advisor"
            self.filters["include_tasks"] = 1
        elif based_on == "Job Controller":
            self.filters["group_by_1"] = "Group by Job Controller"
            self.filters["include_tasks"] = 1

    def _load_source_reports(self):
        based_on = self.filters.get("based_on")

        if based_on == "Service Advisor":
            workshop_turnover_report = WorkshopTurnoverReport(self.filters).run()
            self.workshop_turnover_report_data = workshop_turnover_report[1]
            self._update_columns([])
        else:
            productivity_report = WorkshopProductivityReport(self.filters).run()
            self.data = productivity_report[1]
            self._update_columns(productivity_report[0])

    def _update_columns(self, source_columns):
        for column in source_columns:
            if column.get("fieldname") in HIDDEN_SOURCE_COLUMNS:
                column["hidden"] = 1

        based_on = self.filters.get("based_on")

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

        columns = list(source_columns)
        columns[:0] = columns_map.get(based_on, [])

        incentive_columns = []
        template = BASED_ON_TEMPLATE_DATA.get(based_on) or {}
        if template.get("weightages"):
            incentive_columns = [
                {
                    "label": format_label(field) + " Amt",
                    "fieldname": field + "_amt",
                    "fieldtype": "Float",
                    "width": 150,
                }
                for field in template["weightages"]
            ]

        if based_on in ("Reporting Authority", "Technician"):
            columns.append(
                {
                    "label": "Sold Hrs. %",
                    "fieldname": "sold_hrs_percentage",
                    "fieldtype": "Float",
                    "width": 100,
                }
            )

        if based_on == "Reporting Authority":
            columns.append(
                {
                    "label": "QC RO %",
                    "fieldname": "total_qc_ro_percentage",
                    "fieldtype": "Float",
                    "width": 100,
                }
            )

        if based_on == "Job Controller":
            columns.append(
                {
                    "label": "Idle %",
                    "fieldname": "total_idle_percentage",
                    "fieldtype": "Percentage",
                    "width": 100,
                }
            )
            columns.append(
                {
                    "label": "WIP RO Count",
                    "fieldname": "wip_ro_count",
                    "fieldtype": "Int",
                    "width": 100,
                }
            )
            columns.append(
                {
                    "label": "WIP Average Age",
                    "fieldname": "wip_average_age",
                    "fieldtype": "Float",
                    "width": 100,
                }
            )
            columns.append(
                {
                    "label": "K2K Bodyshop Avg. Age",
                    "fieldname": "key_to_key_duration_bodyshop",
                    "fieldtype": "Int",
                    "width": 100,
                }
            )
            columns.append(
                {
                    "label": "K2K Mechanical Avg. Age",
                    "fieldname": "key_to_key_duration_mechanical",
                    "fieldtype": "Int",
                    "width": 100,
                }
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

        self.columns = columns

    def _prepare_lookups(self):
        self.qc_task_types = set(
            frappe.get_all(
                "Task Type", filters={"name": ["like", "%QC%"]}, pluck="name"
            )
        )

        based_on = self.filters.get("based_on")

        if based_on == "Reporting Authority":
            feedback = self._fetch_reporting_authority_feedback() or []
            self.reporting_authority_feedback_map = {
                d.get("reports_to"): d for d in feedback
            }
        elif based_on == "Service Advisor":
            feedback = self._fetch_service_advisor_feedback() or []
            self.service_advisor_feedback_map = {
                d.get("service_advisor"): d for d in feedback
            }
            self.wip_average_age_sa = self._fetch_service_advisor_wip_age() or []
            self.target_sa = self._fetch_service_advisor_targets()
            self.allowed_service_advisors = (
                self._fetch_service_advisors_by_designation()
            )
        elif based_on == "Job Controller":
            self.wip_average_age_jc = self._fetch_job_controller_wip_age() or []
            self._fetch_job_controller_key_to_key_mechanical = (
                self._fetch_job_controller_key_to_key("Mechanical")
            )
            self._fetch_job_controller_key_to_key_bodyshop = (
                self._fetch_job_controller_key_to_key("Body Shop")
            )

    def _fetch_reporting_authority_feedback(self):
        condition_dict = {
            "from_dt": self.filters.get("from_date"),
            "to_dt": self.filters.get("to_date"),
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

    def _fetch_service_advisor_feedback(self):
        condition_dict = {
            "from_dt": self.filters.get("from_date"),
            "to_dt": self.filters.get("to_date"),
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

    def _fetch_service_advisors_by_designation(self):
        settings = frappe.get_cached_doc("Incentive Calculation Setttings")
        designations = [
            d.designation
            for d in (settings.service_advisor_designation or [])
            if d.designation
        ]
        if not designations:
            return None

        rows = frappe.db.sql(
            """
            select sp.name
            from `tabSales Person` sp
            inner join `tabEmployee` emp on emp.user_id = sp.user_id
            where sp.is_service_advisor = 1
              and sp.enabled = 1
              and emp.designation in %(designations)s
            """,
            {"designations": tuple(designations)},
            as_dict=True,
        )
        return {row.name for row in rows}

    def _fetch_service_advisor_targets(self):
        to_date = getdate(self.filters.get("to_date") or getdate())
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

        return {
            row.get("service_advisor"): flt(row.get("target_amount")) for row in rows
        }

    def _fetch_service_advisor_wip_age(self):
        as_of = getdate(self.filters.get("to_date") or getdate())

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

    def _fetch_job_controller_wip_age(self):
        as_of = getdate(self.filters.get("to_date") or getdate())

        return frappe.db.sql(
            """
            select
                p.job_controller,
                count(p.name) as ro_count,
                round(avg(datediff(%(as_of)s, date(p.project_date))), 2) as average_wip_age
            from
                `tabProject` p
            where
                p.status != 'Cancelled'
                and p.project_status != 'Completed'
                and p.job_controller is not null
                and p.job_controller != ''
                and p.project_date <= %(as_of)s
            group by
                p.job_controller;
            """,
            {"as_of": as_of},
            as_dict=True,
        )

    def _fetch_job_controller_key_to_key(self, workshop_division):
        self.filters["workshop_division"] = workshop_division
        key_to_key_report = VehicleKeyToKeyReport(self.filters).run()
        return key_to_key_report[1]

    def _process_rows(self):
        based_on = self.filters.get("based_on")

        if based_on == "Service Advisor":
            if self.workshop_turnover_report_data:
                yield from service_advisor_process_rows(
                    self.filters,
                    self.workshop_turnover_report_data,
                    self.service_advisor_feedback_map,
                    self.wip_average_age_sa,
                    self.target_sa,
                    self.allowed_service_advisors,
                )

        for each_data in self.data:
            if each_data.get("sold_time") and each_data.get("available_hours"):
                each_data["sold_hrs_percentage"] = flt(
                    (each_data.get("sold_time") / each_data.get("available_hours"))
                    * 100.0,
                    3,
                )
            else:
                each_data["sold_hrs_percentage"] = 0.0

            for each_group_rows in each_data.rows:
                totals_dict = each_group_rows.totals or {}

                ro_set, qc_ro_set = set(), set()
                for row in each_group_rows.rows or []:
                    if row.get("task_type") in self.qc_task_types:
                        qc_ro_set.add(row.get("project"))
                    else:
                        ro_set.add(row.get("project"))

                if totals_dict.get("sold_time") and totals_dict.get("available_hours"):
                    totals_dict["sold_hrs_percentage"] = flt(
                        (
                            totals_dict.get("sold_time")
                            / totals_dict.get("available_hours")
                        )
                        * 100.0,
                        3,
                    )
                else:
                    totals_dict["sold_hrs_percentage"] = 0.0

                self._compute_sold_hrs_amount(totals_dict)
                self._compute_efficiency_amount(totals_dict)
                self._compute_productivity_amount(totals_dict)
                self._compute_proficiency_amount(totals_dict)

                totals_dict["total_ro_count_non_qc"] = len(ro_set)
                totals_dict["total_qc_ro_count"] = len(qc_ro_set)
                totals_dict["total_qc_ro_percentage"] = flt(
                    (len(qc_ro_set) / (len(ro_set) + len(qc_ro_set))) * 100.0, 3
                )

                self._compute_qc_ro_amount(totals_dict)

                if totals_dict.get("_bold"):
                    totals_dict["_bold"] = 0

                if based_on == "Reporting Authority":
                    self._compute_reporting_authority_feedback(totals_dict)
                    if not totals_dict.get("reports_to"):
                        continue

                if based_on == "Job Controller":
                    if not totals_dict.get("job_controller"):
                        continue
                    totals_dict["total_idle_percentage"] = flt(
                        (
                            flt(
                                flt(totals_dict.get("available_hours"))
                                - flt(totals_dict.get("actual_time"))
                                - flt(totals_dict.get("out_of_shift_hours"))
                            )
                            / flt(totals_dict.get("available_hours"))
                        )
                        * 100.0,
                        3,
                    )
                    self._compute_idle_amount(totals_dict)
                    job_controller = totals_dict.get("job_controller")
                    totals_dict["wip_ageing_amt"] = 0.0
                    totals_dict["wip_ro_count"] = 0

                    for each_job_controller_wip_average_age in self.wip_average_age_jc:
                        if (
                            each_job_controller_wip_average_age.get("job_controller")
                            == job_controller
                        ):
                            totals_dict["wip_average_age"] = flt(
                                each_job_controller_wip_average_age.get(
                                    "average_wip_age"
                                )
                            )
                            totals_dict["wip_ro_count"] = flt(
                                each_job_controller_wip_average_age.get("ro_count")
                            )
                            if flt(totals_dict["wip_average_age"]) <= 46.0:
                                wip_average_age_weightage_amount = (
                                    get_weightage_amount(
                                        based_on=self.filters.get("based_on"),
                                        base_incentive=self.filters.get(
                                            "base_incentive"
                                        ),
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
                                based_on=self.filters.get("based_on"),
                                base_incentive=self.filters.get("base_incentive"),
                                field_name="wip_ageing",
                            )
                            or 0
                        )
                        totals_dict["wip_ageing_amt"] = flt(
                            wip_average_age_weightage_amount,
                            3,
                        )
                    total_age_key_to_key_bodyshop = 0
                    total_number_of_key_to_key_ro_bodyshop = len(
                        self._fetch_job_controller_key_to_key_bodyshop
                    )
                    for (
                        each_job_controller_key_to_key_bodyshop
                    ) in self._fetch_job_controller_key_to_key_bodyshop:
                        if (
                            each_job_controller_key_to_key_bodyshop.get(
                                "job_controller"
                            )
                            == job_controller
                        ):
                            total_age_key_to_key_bodyshop += (
                                int(each_job_controller_key_to_key_bodyshop.get("age"))
                                if each_job_controller_key_to_key_bodyshop.get("age")
                                else 0
                            )
                    else:
                        totals_dict["key_to_key_duration_bodyshop"] = int(
                            total_age_key_to_key_bodyshop
                            / total_number_of_key_to_key_ro_bodyshop
                        )

                    total_age_key_to_key_mechanical = 0
                    total_number_of_key_to_key_ro_mechanical = len(
                        self._fetch_job_controller_key_to_key_mechanical
                    )
                    for (
                        each_job_controller_key_to_key_mechanical
                    ) in self._fetch_job_controller_key_to_key_mechanical:
                        if (
                            each_job_controller_key_to_key_mechanical.get(
                                "job_controller"
                            )
                            == job_controller
                        ):
                            total_age_key_to_key_mechanical += (
                                int(
                                    each_job_controller_key_to_key_mechanical.get("age")
                                )
                                if each_job_controller_key_to_key_mechanical.get("age")
                                else 0
                            )
                    else:
                        totals_dict["key_to_key_duration_mechanical"] = int(
                            total_age_key_to_key_bodyshop
                            / total_number_of_key_to_key_ro_mechanical
                        )

                totals_dict["calculated_incentive"] = compute_incentive(
                    totals_dict, based_on
                )
                yield totals_dict

    def _weightage_amount(self, field_name):
        return (
            get_weightage_amount(
                based_on=self.filters.get("based_on"),
                base_incentive=self.filters.get("base_incentive"),
                field_name=field_name,
            )
            or 0
        )

    def _compute_sold_hrs_amount(self, totals):
        result = get_ladder_result(
            based_on=self.filters.get("based_on"),
            sold_hrs_percentage=totals.get("sold_hrs_percentage"),
            ladder_field="sold_hrs_ladder",
            top_cap=125.0,
        )
        if result:
            totals["sold_hrs_amt"] = flt(
                self._weightage_amount("sold_hrs") * (result / 100.0), 3
            )
        else:
            totals["sold_hrs_amt"] = 0

    def _compute_efficiency_amount(self, totals):
        result = get_ladder_result(
            based_on=self.filters.get("based_on"),
            sold_hrs_percentage=totals.get("per_efficiency"),
            ladder_field="efficiency_ladder",
            top_cap=125.0,
        )
        if result:
            totals["efficiency_amt"] = flt(
                self._weightage_amount("efficiency") * (result / 100.0), 3
            )
        else:
            totals["efficiency_amt"] = 0

    def _compute_productivity_amount(self, totals):
        result = get_ladder_result(
            based_on=self.filters.get("based_on"),
            sold_hrs_percentage=totals.get("per_productivity"),
            ladder_field="productivity_ladder",
            top_cap=125.0,
        )
        if result:
            totals["productivity_amt"] = flt(
                self._weightage_amount("productivity") * (result / 100.0), 3
            )
        else:
            totals["productivity_amt"] = 0

    def _compute_proficiency_amount(self, totals):
        result = get_ladder_result(
            based_on=self.filters.get("based_on"),
            sold_hrs_percentage=totals.get("per_proficiency"),
            ladder_field="proficiency_ladder",
            top_cap=125.0,
        )
        if result:
            totals["proficiency_amt"] = flt(
                self._weightage_amount("proficiency") * (result / 100.0), 3
            )
        else:
            totals["proficiency_amt"] = 0

    def _compute_qc_ro_amount(self, totals):
        result = get_rate_ladder_result(
            based_on=self.filters.get("based_on"),
            percentage=totals.get("total_qc_ro_percentage"),
            ladder_field="qc_ro_ladder",
            top_cap=10.0,
        )
        if result:
            totals["qc_ro_amt"] = flt(
                self._weightage_amount("qc_ro") * (result / 100.0), 3
            )
        else:
            totals["qc_ro_amt"] = 0

    def _compute_idle_amount(self, totals):
        result = get_rate_ladder_result(
            based_on=self.filters.get("based_on"),
            percentage=totals.get("total_idle_percentage"),
            ladder_field="idle_time_ladder",
            top_cap=10.0,
        )
        if result:
            totals["idle_time_amt"] = flt(
                self._weightage_amount("idle_time") * (result / 100.0), 3
            )
        else:
            totals["idle_time_amt"] = 0

    def _compute_reporting_authority_feedback(self, totals):
        totals["customer_feedback_amt"] = 0
        reports_to = totals.get("reports_to")
        if not reports_to or reports_to not in self.reporting_authority_feedback_map:
            return

        cfb = self.reporting_authority_feedback_map[reports_to]
        if not cfb.get("avg_rating"):
            return

        rating = flt(cfb.get("avg_rating"), 2)
        totals["customer_overall_rating"] = rating
        totals["customer_overall_rating_value"] = rating
        rating_out_of_five = flt((rating / 2) * 10.0, 2)
        totals["ro_count_cfb"] = cfb.get("ro_count")

        result = get_rate_ladder_result(
            based_on=self.filters.get("based_on"),
            percentage=rating_out_of_five,
            ladder_field="cfb_rate_ladder",
            top_cap=5.0,
        )
        if result:
            totals["customer_feedback_amt"] = flt(
                self._weightage_amount("customer_feedback") * (result / 100.0), 3
            )
        else:
            totals["customer_feedback_amt"] = 0

    def _build_summary_html(self):
        based_on = self.filters.get("based_on")
        base_incentive = self.filters.get("base_incentive")

        based_on_html_table = generate_weightage_table(based_on, base_incentive)

        ladder_specs = [
            ("sold_hrs_ladder", "Sold Hrs %", "percent", None),
            ("efficiency_ladder", "Efficiency %", "percent", None),
            ("productivity_ladder", "Productivity %", "percent", None),
            ("proficiency_ladder", "Proficiency %", "percent", None),
            ("qc_ro_ladder", "QC RO", "rate", "%"),
            ("revenue_ladder", "Revenue", "rate", None),
            ("cfb_rate_ladder", "Customer Feedback Rate", "rate", None),
            ("wip_ageing_ladder", "Average WIP Ageing", "rate", None),
            ("idle_time_ladder", "Idle", "rate", "%"),
            ("key_to_key_mechanical_ladder", "K2K Mechanical", "rate", None),
            ("key_to_key_bodyshop_ladder", "K2K Bodyshop", "rate", None),
        ]

        ladder_html_tables = []
        for ladder_field, label, kind, suffix in ladder_specs:
            if kind == "percent":
                html = generate_ladder_html(based_on, ladder_field, label)
            elif suffix is not None:
                html = rate_based_generate_ladder_html(
                    based_on, ladder_field, label, suffix
                )
            else:
                html = rate_based_generate_ladder_html(based_on, ladder_field, label)
            if html:
                ladder_html_tables.append(html)

        if not (based_on_html_table or ladder_html_tables):
            return ""

        summary_html = """
        <table style="
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
        ">
            <tr>
        """

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

        if ladder_html_tables:
            summary_html += """
                <td style="
                    width: 75%;
                    vertical-align: top;
                    padding: 5px;
                ">
            """
            for html in ladder_html_tables:
                summary_html += f"""
                    <div style="
                        width: 100%;
                        margin-bottom: 10px;
                    ">
                        {html}
                    </div>
                """
            summary_html += """
                </td>
            """

        summary_html += """
            </tr>
        </table>
        """

        return f"""
        <details style="
            border: 1px solid #d1d8dd;
            border-radius: 6px;
            padding: 8px 12px;
            margin-bottom: 10px;
            background: #fafbfc;
        ">
            <summary style="
                cursor: pointer;
                font-weight: 600;
                font-size: 14px;
                color: #1f272e;
                list-style: none;
                display: flex;
                align-items: center;
                gap: 6px;
                user-select: none;
            ">
                <span class="incentive-summary-caret" style="
                    display: inline-block;
                    transition: transform 0.15s ease;
                ">&#9656;</span>
                Incentive Calculation Criteria
            </summary>
            <style>
                details[open] .incentive-summary-caret {{
                    transform: rotate(90deg);
                }}
                summary::-webkit-details-marker {{ display: none; }}
            </style>
            <div style="margin-top: 10px;">
                {summary_html}
            </div>
        </details>
        """
