# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

"""Employee Incentive Calculation report.

This module is the orchestrator only: it picks the `util_<designation>` module
matching the `based_on` filter and drives it through a fixed sequence — apply
the source report filters, load the source data, prepare the lookups, process
the rows. Every designation specific column, query and calculation lives in its
own module:

    util_technician.py
    util_service_advisor.py
    util_team_lead.py
    util_job_controller.py
    util_quality_controller.py
    util_bodyshop_estimator.py
    util_insurance_bd.py

Each of those exposes the same small interface: TEMPLATE_DATA, REPORT_FILTERS,
SOURCE_REPORT, get_leading_columns(), get_trailing_columns(),
prepare_lookups(filters) and
process_rows(filters, source_data, qc_task_types, lookups).
"""

import frappe
from automotive.automotive.report.workshop_productivity.workshop_productivity import (
    WorkshopProductivityReport,
)
from automotive.automotive.report.workshop_turnover.workshop_turnover import (
    WorkshopTurnoverReport,
)

from . import (
    util_bodyshop_estimator,
    util_insurance_bd,
    util_job_controller,
    util_quality_controller,
    util_service_advisor,
    util_team_lead,
    util_technician,
)
from .html_generator_employee_incentive_calculation import (
    generate_ladder_html,
    generate_weightage_table,
    rate_based_generate_ladder_html,
)

DESIGNATION_UTILS = {
    "Technician": util_technician,
    "Team Lead": util_team_lead,
    "Service Advisor": util_service_advisor,
    "Job Controller": util_job_controller,
    "Quality Controller": util_quality_controller,
    "Bodyshop Estimator": util_bodyshop_estimator,
    "Insurance BD": util_insurance_bd,
}

# Assembled from the designation modules so each one owns its own weightages
# and ladders. Read by the ladder helpers and the summary HTML generator.
BASED_ON_TEMPLATE_DATA = {
    based_on: module.TEMPLATE_DATA for based_on, module in DESIGNATION_UTILS.items()
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
    "job_controller",
    "job_controller_name",
}

LADDER_SPECS = [
    ("sold_hrs_ladder", "Sold Hrs %", "percent", None),
    ("efficiency_ladder", "Efficiency %", "percent", None),
    ("productivity_ladder", "Productivity %", "percent", None),
    ("proficiency_ladder", "Proficiency %", "percent", None),
    ("qc_ro_ladder", "QC RO", "rate", "%"),
    ("revenue_ladder", "Revenue %", "percent", None),
    ("cfb_rate_ladder", "Customer Feedback Rate", "rate", None),
    ("wip_ageing_ladder", "Average WIP Ageing", "rate", None),
    ("idle_time_ladder", "Idle", "rate", "%"),
    ("key_to_key_mechanical_ladder", "K2K Mechanical", "rate", None),
    ("key_to_key_bodyshop_ladder", "K2K Bodyshop", "rate", None),
    ("come_back_ro_ladder", "Come Back RO", "rate", "%"),
    ("invoiced_ro_ladder", "Invoiced RO %", "percent", None),
    ("gross_profit_ladder", "Gross Profit", "rate", "%"),
    ("estimate_to_approval_ladder", "Estimate to Approval", "rate", "%"),
    ("labour_parts_mix_ladder", "Labour Parts Mix", "rate", "%"),
]


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
        self.module = DESIGNATION_UTILS.get(self.filters.get("based_on"))
        self.columns = []
        self.source_data = []
        self.source_columns = []
        self.qc_task_types = set()
        self.lookups = {}

    def run(self):
        self._apply_based_on_filters()
        self._load_source_reports()
        self._update_columns()
        self._prepare_lookups()

        filtered_data = [row for row in self._process_rows() if ("_summary" not in row)]
        summary_html = self._build_summary_html()

        return (self.columns, filtered_data, summary_html, None, None)

    def _apply_based_on_filters(self):
        if self.module:
            self.filters.update(self.module.REPORT_FILTERS)

    def _load_source_reports(self):
        source_report = self.module.SOURCE_REPORT if self.module else None

        if source_report == "turnover":
            turnover_report = WorkshopTurnoverReport(self.filters).run()
            self.source_data = turnover_report[1]
        elif source_report == "productivity":
            productivity_report = WorkshopProductivityReport(self.filters).run()
            self.source_data = productivity_report[1]
            self.source_columns = productivity_report[0]

    def _update_columns(self):
        for column in self.source_columns:
            if column.get("fieldname") in HIDDEN_SOURCE_COLUMNS:
                column["hidden"] = 1

        columns = list(self.source_columns)

        if self.module:
            columns[:0] = self.module.get_leading_columns()
            columns.extend(self.module.get_trailing_columns())

            weightages = self.module.TEMPLATE_DATA.get("weightages") or {}
            columns.extend(
                {
                    "label": format_label(field) + " Amt",
                    "fieldname": field + "_amt",
                    "fieldtype": "Float",
                    "width": 150,
                }
                for field in weightages
            )

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

        if self.module:
            self.lookups = self.module.prepare_lookups(self.filters) or {}

    def _process_rows(self):
        if not self.module:
            return iter([])

        return self.module.process_rows(
            self.filters,
            self.source_data,
            self.qc_task_types,
            self.lookups,
        )

    def _build_summary_html(self):
        based_on = self.filters.get("based_on")
        base_incentive = self.filters.get("base_incentive") or 0.0

        based_on_html_table = generate_weightage_table(based_on, base_incentive)

        ladder_html_tables = []
        for ladder_field, label, kind, suffix in LADDER_SPECS:
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
