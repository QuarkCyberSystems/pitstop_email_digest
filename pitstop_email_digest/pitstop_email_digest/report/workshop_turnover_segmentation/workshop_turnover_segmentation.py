# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt
import datetime

import erpnext
import frappe
from erpnext.accounts.report.gross_profit.gross_profit import (
    update_item_valuation_rates,
)
from erpnext.projects.doctype.timesheet.timesheet import get_activity_cost
from erpnext.setup.doctype.item_group.item_group import get_item_group_subtree
from erpnext.stock.doctype.item.item import convert_item_uom_for
from frappe import _, scrub, unscrub
from frappe.desk.query_report import group_report_data
from frappe.utils import cint, combine_datetime, cstr, flt, getdate, nowdate


def execute(filters=None):
    return WorkshopTurnoverReport(filters).run()


class WorkshopTurnoverReport:
    total_fields = [
        "total_sales_amount",
        "hourly_labour_sales_amount",
        "package_sales_amount",
        "sublet_sales_amount",
        "part_sales_amount",
        "lubricant_sales_amount",
        "consumble_sales_amount",
        "material_sales_amount",
        "paint_sales_amount",
        "timesheet_costing_amount",
        "total_unproductive_cost",
        "parts_cogs",
        "parts_gross_profit",
        "total_gross_profit",
        "total_consumed_material_cost",
        "total_purchase_cost",
        # "vehicle_throughput",
        # "open_repair_orders",
        # "closed_repair_orders",
        "sold_time",
    ]

    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})

        self.total_unproductive_cost_data = frappe._dict(
            {
                "total_available_time": 0,
                "total_unproductive_time": 0,
                "total_unproductive_cost": 0,
            }
        )

    def run(self):
        self.validate_filters()
        self.get_invoice_data()

        data = self.get_grouped_data()
        columns = self.get_columns()

        totals = self.calculate_overall_totals()
        totals_summary = self.get_totals_summary(totals)

        return columns, data, None, None, totals_summary

    def validate_filters(self):
        self.filters.from_date = getdate(self.filters.from_date or nowdate())
        self.filters.to_date = getdate(self.filters.to_date or nowdate())

        self.filters.from_dt = combine_datetime(self.filters.from_date, datetime.time.min)
        self.filters.to_dt = combine_datetime(self.filters.to_date, datetime.time.max)

        if self.filters.from_date > self.filters.to_date:
            frappe.throw(_("From Date must be before To Date"))

    def get_invoice_data(self):
        conditions = self.get_conditions()
        conditions_str = " and " + " and ".join(conditions) if conditions else ""

        projects_settings = frappe.get_cached_doc("Projects Settings", None)

        # Invoice Data
        invoice_data = frappe.db.sql(
            f"""
			select
				inv.name as sales_invoice, inv.posting_date, inv.is_return,
				i.project, p.final_invoice_date, p.company,
				p.vehicle_workshop, p.branch, p.cost_center, p.vehicle_workshop_division, p.service_advisor,
				i.item_code, i.item_group, i.is_stock_item, i.is_fixed_asset,
				i.qty, i.uom, i.stock_uom, i.conversion_factor,
				i.base_net_amount as net_amount,

				p.customer_group, p.bill_to_customer_group,

				inv.bill_to, dn_item.claim_customer, dn_item.discount_percentage as claim_discount_percentage,

				i.delivery_note_item, i.batch_no, inv.update_stock, inv.docstatus,
				inv.depreciation_type, i.ignore_depreciation, i.depreciation_percentage,
				'Sales Invoice' as parenttype, i.name as child_docname
			from `tabSales Invoice Item` i
			inner join `tabSales Invoice` inv on inv.name = i.parent
			left join `tabDelivery Note Item` dn_item on dn_item.name = i.delivery_note_item
			inner join `tabProject` p on p.name = i.project
			where inv.docstatus = 1
				and inv.posting_date between %(from_date)s and %(to_date)s
				{conditions_str}
			order by p.final_invoice_date, inv.posting_date
		""",
            self.filters,
            as_dict=1,
        )

        # Project Data
        project_names = list(set([d.project for d in invoice_data]))
        project_data = []
        if project_names:
            project_data = frappe.db.sql(
                """
				select p.name as project,
					p.total_consumed_material_cost,
					p.timesheet_costing_amount,
					p.total_purchase_cost
				from `tabProject` p
				where p.name in %s
			""",
                [project_names],
                as_dict=1,
            )

        # Material COGS
        update_item_valuation_rates(invoice_data, get_last_purchase_rate=False)
        for d in invoice_data:
            d.split_percentage = 100

            if d.depreciation_type and not d.ignore_depreciation:
                d.split_percentage = 100 - d.depreciation_percentage if d.depreciation_type == "After Depreciation Amount" else d.depreciation_percentage

            if d.claim_customer:
                if d.claim_customer != d.bill_to:
                    d.split_percentage *= flt(d.claim_discount_percentage) / 100
                else:
                    d.split_percentage *= 1 - (flt(d.claim_discount_percentage) / 100)

            d.cogs_per_unit = flt(d.valuation_rate) * flt(d.conversion_factor)
            d.cogs_per_unit = d.cogs_per_unit * d.split_percentage / 100
            d.cogs = d.cogs_per_unit * d.qty

        # Item Groups
        materials_item_groups = []
        lubricants_item_groups = []
        consumables_item_groups = []
        sublet_item_groups = []
        paint_item_groups = []
        if projects_settings.materials_item_group:
            materials_item_groups = get_item_group_subtree(projects_settings.materials_item_group)
        if projects_settings.lubricants_item_group:
            lubricants_item_groups = get_item_group_subtree(projects_settings.lubricants_item_group)
        if projects_settings.consumables_item_group:
            consumables_item_groups = get_item_group_subtree(projects_settings.consumables_item_group)
        if projects_settings.sublet_item_group:
            sublet_item_groups = get_item_group_subtree(projects_settings.sublet_item_group)
        if projects_settings.paint_item_group:
            paint_item_groups = get_item_group_subtree(projects_settings.paint_item_group)

        # Project Wise Totals
        project_map = {}
        for d in invoice_data:
            if d.project not in project_map:
                project_map[d.project] = self.get_row_template(d)

            obj = project_map[d.project]
            obj.total_sales_amount += d.net_amount
            obj.parts_cogs += d.cogs

            if d.is_stock_item or d.item_group in materials_item_groups:
                obj.material_sales_amount += d.net_amount

                if d.item_group in lubricants_item_groups:
                    obj.lubricant_sales_amount += d.net_amount
                elif d.item_group in paint_item_groups:
                    obj.paint_sales_amount += d.net_amount
                elif d.item_group in consumables_item_groups:
                    obj.consumble_sales_amount += d.net_amount
                else:
                    obj.part_sales_amount += d.net_amount
            else:
                if d.item_group in sublet_item_groups:
                    obj.sublet_sales_amount += d.net_amount
                else:
                    if d.uom == "Hour" or d.stock_uom == "Hour":
                        obj.hourly_labour_sales_amount += d.net_amount
                    else:
                        obj.package_sales_amount += d.net_amount

                    hours = convert_item_uom_for(
                        d.qty,
                        d.item_code,
                        d.uom,
                        "Hour",
                        conversion_factor=d.conversion_factor if d.stock_uom == "Hour" else None,
                        null_if_not_convertible=True,
                    )
                    if hours is not None:
                        obj.sold_time += hours

        for d in project_data:
            if d.project not in project_map:
                continue

            obj = project_map[d.project]
            obj.total_consumed_material_cost += d.total_consumed_material_cost
            obj.timesheet_costing_amount += d.timesheet_costing_amount
            obj.total_purchase_cost += d.total_purchase_cost

        self.invoice_data = list(project_map.values())

        for d in self.invoice_data:
            self.postprocess_row(d)

        return self.invoice_data

    def get_row_template(self, d):
        obj = frappe._dict(
            {
                "reference_type": "Project",
                "reference": d.project,
                "project": d.project,
                "final_invoice_date": d.final_invoice_date,
                "vehicle_workshop": d.vehicle_workshop,
                "branch": d.branch,
                "cost_center": d.cost_center,
                "vehicle_workshop_division": d.vehicle_workshop_division,
                "service_advisor": d.service_advisor,
                "customer_group": d.bill_to_customer_group or d.customer_group,
            }
        )
        for field in self.total_fields:
            obj[field] = 0

        return obj

    def get_conditions(self):
        conditions = []

        if self.filters.get("company"):
            conditions.append("p.company = %(company)s")

        if self.filters.get("vehicle_workshop"):
            conditions.append("p.vehicle_workshop = %(vehicle_workshop)s")

        if self.filters.get("branch"):
            conditions.append("p.branch = %(branch)s")

        if self.filters.get("cost_center"):
            conditions.append("p.cost_center = %(cost_center)s")

        if self.filters.get("vehicle_workshop_division"):
            conditions.append("p.vehicle_workshop_division = %(vehicle_workshop_division)s")

        if self.filters.get("service_advisor"):
            conditions.append("p.service_advisor = %(service_advisor)s")

        if self.filters.get("customer_group"):
            lft, rgt = frappe.db.get_value("Customer Group", self.filters.customer_group, ["lft", "rgt"])
            conditions.append(
                f"""
				if(ifnull(p.bill_to_customer_group, '') = '', p.customer_group, p.bill_to_customer_group) in (
					select name from `tabCustomer Group` where lft >= {lft} and rgt <= {rgt}
				)
			"""
            )

        if self.filters.get("segmentation"):
            if self.filters.get("segmentation") == "BRAC-QIC":
                conditions.append("p.customer_group = 'Budget Mobility' and " "p.bill_to_customer_group = 'Insurance' and p.vehicle_workshop_division = 'Body Shop'")
            if self.filters.get("segmentation") == "BRAC-CASH":
                conditions.append("p.customer_group = 'Budget Mobility' and " "p.bill_to_customer_group != 'Insurance' and p.vehicle_workshop_division = 'Body Shop'")
            if self.filters.get("segmentation") == "BRAC-MECH.":
                conditions.append("p.customer_group = 'Budget Mobility' and p.vehicle_workshop_division = 'Mechanical'")
            if self.filters.get("segmentation") == "TESLA":
                conditions.append(
                    f"""
						'TESLA' in (
							select
								ti.brand
							from
								`tabItem` ti
							where
								ti.name = p.applies_to_item
						) and p.vehicle_workshop_division = 'Body Shop'
					"""
                )
            if self.filters.get("segmentation") == "AGMC-GEELY":
                conditions.append(
                    f"""
						'GEELY' in (
							select
								ti.brand
							from
								`tabItem` ti
							where
								ti.name = p.applies_to_item
						) and p.vehicle_workshop_division = 'Body Shop' and p.bill_to_customer_group = 'AGMC - Geely'
					"""
                )

        return conditions

    def get_grouped_data(self):
        data = self.invoice_data

        self.group_by = [None]
        for i in range(2):
            group_label = self.filters.get("group_by_" + str(i + 1), "").replace("Group by ", "")

            if not group_label:
                continue

            if group_label == "Workshop Division":
                group_field = "vehicle_workshop_division"
            else:
                group_field = scrub(group_label)

            self.group_by.append(group_field)

        if len(self.group_by) <= 1:
            return data

        return group_report_data(
            data,
            self.group_by,
            calculate_totals=self.calculate_group_totals,
            postprocess_group=self.postprocess_group,
            totals_only=self.filters.totals_only,
        )

    def calculate_group_totals(self, data, group_field, group_value, grouped_by):
        totals = frappe._dict()

        # Copy grouped by into total row
        for f, g in grouped_by.items():
            totals[f] = g

        # Set zeros
        for f in self.total_fields:
            totals[f] = 0

        # Add totals
        for d in data:
            for f in self.total_fields:
                totals[f] += flt(d.get(f))

        # Set reference field
        reference_field = group_field[0] if isinstance(group_field, (list, tuple)) else group_field
        reference_dt = unscrub(cstr(reference_field))
        totals["reference_type"] = reference_dt
        totals["reference"] = grouped_by.get(reference_field) if group_field else "Total"

        if not group_field and self.group_by == [None]:
            totals["parent"] = "'Total'"

        if group_field == "vehicle_workshop" and group_value and len(grouped_by) <= 2 and not self.filters.get("customer_group"):
            self.set_unproductive_labour_cost(totals, group_value)

        self.postprocess_row(totals)
        self.set_throughput_and_open_repair_orders(totals, grouped_by)
        return totals

    def calculate_overall_totals(self):
        totals = frappe._dict({"currency": erpnext.get_company_currency(self.filters.company)})

        for field in self.total_fields:
            totals[field] = 0

        for d in self.invoice_data:
            for field in self.total_fields:
                totals[field] += flt(d.get(field))

        totals.update(self.total_unproductive_cost_data)

        self.postprocess_row(totals)
        self.set_throughput_and_open_repair_orders(totals, {})

        return totals

    def get_totals_summary(self, totals):
        if not totals:
            return None

        return [
            {
                "label": _("Total Sales"),
                "value": totals.total_sales_amount,
                "indicator": "green",
                "datatype": "Currency",
            },
            {
                "label": _("Service Sales"),
                "value": totals.hourly_labour_sales_amount + totals.package_sales_amount,
                "indicator": "blue",
                "datatype": "Currency",
            },
            {
                "label": _("Total Labour Cost"),
                "value": totals.total_labour_cost,
                "indicator": "orange",
                "datatype": "Currency",
            },
            {
                "label": _("Labour GP"),
                "value": totals.labour_gross_profit,
                "indicator": "blue",
                "datatype": "Currency",
            },
            {
                "label": _("Labour GP (%)"),
                "value": flt(totals.labour_profit_margin, 1),
                "indicator": "blue",
                "datatype": "Percent",
                "precision": 1,
            },
            {
                "label": _("Material Sales"),
                "value": totals.material_sales_amount,
                "indicator": "blue",
                "datatype": "Currency",
            },
            {
                "label": _("Parts CoS"),
                "value": totals.parts_cogs,
                "indicator": "red",
                "datatype": "Currency",
            },
            {
                "label": _("Parts GP"),
                "value": totals.parts_gross_profit,
                "indicator": "blue",
                "datatype": "Currency",
            },
            {
                "label": _("Parts GP (%)"),
                "value": flt(totals.parts_profit_margin, 1),
                "indicator": "blue",
                "datatype": "Percent",
                "precision": 1,
            },
            {
                "label": _("Consumed Materal Cost"),
                "value": totals.total_consumed_material_cost,
                "indicator": "red",
                "datatype": "Currency",
            },
            {
                "label": _("Sublet/Purchase Cost"),
                "value": totals.total_purchase_cost,
                "indicator": "red",
                "datatype": "Currency",
            },
            {
                "label": _("Total GP"),
                "value": totals.total_gross_profit,
                "indicator": "green",
                "datatype": "Currency",
            },
            {
                "label": _("Total GP (%)"),
                "value": flt(totals.total_profit_margin, 1),
                "indicator": "green",
                "datatype": "Percent",
                "precision": 1,
            },
            {
                "label": _("Throughput"),
                "value": totals.vehicle_throughput,
                "indicator": "purple",
                "datatype": "Int",
            },
            # {
            # 	"label": _("Open ROs"),
            # 	"value": totals.open_repair_orders,
            # 	"indicator": "purple",
            # 	"datatype": "Int",
            # },
            # {
            # 	"label": _("Closed ROs"),
            # 	"value": totals.closed_repair_orders,
            # 	"indicator": "purple",
            # 	"datatype": "Int",
            # },
            {
                "label": _("Total Sold Hours"),
                "value": totals.sold_time,
                "indicator": "blue",
                "datatype": "Float",
                "precision": 1,
            },
            {
                "label": _("Effective Labour Rate"),
                "value": totals.effective_labour_rate,
                "indicator": "blue",
                "datatype": "Currency",
            },
        ]

    def postprocess_group(self, group_object, grouped_by):
        if not group_object.group_field:
            group_object.totals.update(
                {
                    "total_available_time": sum([flt(d.total_available_time) for d in group_object.rows]),
                    "total_unproductive_time": sum([flt(d.total_unproductive_time) for d in group_object.rows]),
                    "total_unproductive_cost": sum([flt(d.total_unproductive_cost) for d in group_object.rows]),
                }
            )

            self.postprocess_row(group_object.totals)

    def postprocess_row(self, d):
        d.parts_gross_profit = flt(d.material_sales_amount) - flt(d.parts_cogs)
        d.parts_profit_margin = d.parts_gross_profit / flt(d.material_sales_amount) * 100 if flt(d.material_sales_amount) else 0

        d.total_labour_cost = flt(d.timesheet_costing_amount) + flt(d.total_unproductive_cost)

        d.labour_gross_profit = flt(d.hourly_labour_sales_amount) - d.total_labour_cost
        d.labour_profit_margin = d.labour_gross_profit / flt(d.hourly_labour_sales_amount) * 100 if flt(d.hourly_labour_sales_amount) else 0

        d.total_gross_profit = flt(d.total_sales_amount) - flt(d.parts_cogs) - flt(d.total_consumed_material_cost) - flt(d.timesheet_costing_amount) - flt(d.total_purchase_cost)
        d.total_profit_margin = d.total_gross_profit / d.total_sales_amount * 100 if d.total_sales_amount else 0

        if d.sold_time:
            d.effective_labour_rate = d.hourly_labour_sales_amount / d.sold_time
        else:
            d.sold_time = None

    def set_unproductive_labour_cost(self, totals, vehicle_workshop):
        attendance_data = frappe.db.sql(
            """
			select att.employee, sum(available_hours) as available_time
			from `tabAttendance` att
			inner join `tabEmployee` emp on emp.name = att.employee
			where att.docstatus = 1
				and emp.is_technician = 1
				and emp.vehicle_workshop = %(vehicle_workshop)s
				and att.working_hours > 0
				and att.attendance_date between %(from_date)s and %(to_date)s
			group by att.employee
		""",
            {
                "vehicle_workshop": vehicle_workshop,
                "from_date": self.filters.from_date,
                "to_date": self.filters.to_date,
            },
            as_dict=True,
        )

        employee_map = {}
        for d in attendance_data:
            employee_dict = employee_map[d.employee] = d
            employee_dict.actual_time = 0

        employees = list(employee_map.keys())

        timesheet_data = []
        if employees:
            timesheet_data = frappe.db.sql(
                """
				select ts.employee, sum(tsd.hours) as actual_time
				from `tabTimesheet Detail` tsd
				inner join `tabTimesheet` ts on ts.name = tsd.parent
				inner join `tabTask` task on task.name = tsd.task
				where ts.docstatus < 2
					and ts.employee in %(employees)s
					and %(from_dt)s <= tsd.to_time and %(to_dt)s >= tsd.from_time
				group by ts.employee
			""",
                {
                    "employees": employees,
                    "from_dt": self.filters.from_dt,
                    "to_dt": self.filters.to_dt,
                },
                as_dict=1,
            )

        for d in timesheet_data:
            employee_dict = employee_map.get(d.employee)
            employee_dict.actual_time = d.actual_time

        total_available_time = 0
        total_unproductive_time = 0
        total_unproductive_cost = 0

        for employee_dict in employee_map.values():
            total_available_time += employee_dict.available_time

            employee_dict.unproductive_time = employee_dict.available_time - employee_dict.actual_time
            if employee_dict.unproductive_time <= 0:
                continue

            activity_cost = get_activity_cost(employee_dict.name)
            costing_rate = flt(activity_cost.get("costing_rate"))

            total_unproductive_time += employee_dict.unproductive_time
            total_unproductive_cost += employee_dict.unproductive_time * costing_rate

        totals.update(
            {
                "total_available_time": total_available_time,
                "total_unproductive_time": total_unproductive_time,
                "total_unproductive_cost": total_unproductive_cost,
            }
        )

        self.total_unproductive_cost_data.total_available_time += total_available_time
        self.total_unproductive_cost_data.total_unproductive_time += total_unproductive_time
        self.total_unproductive_cost_data.total_unproductive_cost += total_unproductive_cost

    def set_throughput_and_open_repair_orders(self, totals, grouped_by):
        group_fields = {k: v for k, v in grouped_by.items() if k}

        filters = self.filters.copy()
        filters.update(group_fields.copy())
        filters.update(
            {
                "from_date": self.filters.from_date,
                "to_date": self.filters.to_date,
            }
        )

        conditions = self.get_conditions()
        for k, v in group_fields.items():
            if k == "customer_group":
                if v:
                    conditions.append(f"if(ifnull(p.bill_to_customer_group, '') = '', p.customer_group, p.bill_to_customer_group) = %(customer_group)s")
                else:
                    conditions.append(f"ifnull(if(ifnull(p.bill_to_customer_group, '') = '', p.customer_group, p.bill_to_customer_group), '') = ''")
            else:
                if v:
                    conditions.append(f"p.{k} = %({k})s")
                else:
                    conditions.append(f"(p.{k} = '' or {k} is null)")

        conditions_str = " and " + " and ".join(conditions) if conditions else ""

        vehicle_throughput = frappe.db.sql(
            f"""
			select count(*)
			from `tabProject` p
			where p.final_invoice_date between %(from_date)s and %(to_date)s
				and p.status not in ('Draft', 'Cancelled')
				{conditions_str}
		""",
            filters,
        )
        vehicle_throughput = cint(vehicle_throughput[0][0]) if vehicle_throughput else 0

        open_repair_orders = frappe.db.sql(
            f"""
			select count(*)
			from `tabProject` p
			where p.project_date <= %(to_date)s
				and p.status not in ('Draft', 'Cancelled')
				and (p.billing_status != 'Fully Billed' or p.ready_to_close = 0)
				{conditions_str}
		""",
            filters,
        )
        open_repair_orders = cint(open_repair_orders[0][0]) if open_repair_orders else 0

        totals["vehicle_throughput"] = vehicle_throughput
        totals["open_repair_orders"] = open_repair_orders

    def get_columns(self):
        columns = [
            {
                "label": _("Reference"),
                "fieldname": "reference",
                "fieldtype": "Dynamic Link",
                "options": "reference_type",
                "width": 200,
                "column_filter": "has_group",
            },
            {
                "label": _("Date"),
                "fieldname": "final_invoice_date",
                "fieldtype": "Date",
                "width": 80,
            },
            {
                "label": _("Project"),
                "fieldname": "project",
                "fieldtype": "Link",
                "options": "Project",
                "width": 100,
            },
            {
                "label": _("Labour Sales"),
                "fieldname": "hourly_labour_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Package Sales"),
                "fieldname": "package_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Part Sales"),
                "fieldname": "part_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Lubricant Sales"),
                "fieldname": "lubricant_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Consumable Sales"),
                "fieldname": "consumble_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Paint Sales"),
                "fieldname": "paint_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Sublet Sales"),
                "fieldname": "sublet_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Total Sales"),
                "fieldname": "total_sales_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Parts CoS"),
                "fieldname": "parts_cogs",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Parts GP"),
                "fieldname": "parts_gross_profit",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Parts GP (%)"),
                "fieldname": "parts_profit_margin",
                "fieldtype": "Percent",
                "width": 85,
            },
            # {
            # 	"label": _("Target Vs Achievement"),
            # 	"fieldname": "target_acheivement",
            # 	"fieldtype": "Data",
            # 	"width": 80
            # },
            {
                "label": _("Prod. Labour Cost"),
                "fieldname": "timesheet_costing_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Unprod. Labour Cost"),
                "fieldname": "total_unproductive_cost",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Total Labour Cost"),
                "fieldname": "total_labour_cost",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Labour GP"),
                "fieldname": "labour_gross_profit",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Labour GP (%)"),
                "fieldname": "labour_profit_margin",
                "fieldtype": "Percent",
                "width": 95,
            },
            {
                "label": _("Consumed Materials"),
                "fieldname": "total_consumed_material_cost",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Sublet/Purchase Cost"),
                "fieldname": "total_purchase_cost",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 90,
            },
            {
                "label": _("Total GP"),
                "fieldname": "total_gross_profit",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Total GP (%)"),
                "fieldname": "total_profit_margin",
                "fieldtype": "Percent",
                "width": 90,
            },
            {
                "label": _("Throughput"),
                "fieldname": "vehicle_throughput",
                "fieldtype": "Int",
                "width": 80,
            },
            {
                "label": _("Open ROs"),
                "fieldname": "open_repair_orders",
                "fieldtype": "Int",
                "width": 80,
            },
            # {
            # 	"label": _("Closed ROs"),
            # 	"fieldname": "closed_repair_orders",
            # 	"fieldtype": "Int",
            # 	"width": 80
            # },
            {
                "label": _("Hours Sold"),
                "fieldname": "sold_time",
                "fieldtype": "Float",
                "width": 80,
                "precision": 2,
            },
            {
                "label": _("Effective Labour Rate"),
                "fieldname": "effective_labour_rate",
                "fieldtype": "Currency",
                "width": 80,
            },
            {
                "label": _("Avl. Hours"),
                "fieldname": "total_available_time",
                "fieldtype": "Float",
                "width": 80,
                "precision": 2,
            },
            {
                "label": _("Unprod. Hours"),
                "fieldname": "total_unproductive_time",
                "fieldtype": "Float",
                "width": 90,
                "precision": 2,
            },
            {
                "label": _("Vehicle Workshop"),
                "fieldname": "vehicle_workshop",
                "fieldtype": "Link",
                "options": "Vehicle Workshop",
                "width": 120,
            },
            {
                "label": _("Branch"),
                "fieldname": "branch",
                "fieldtype": "Link",
                "options": "Branch",
                "width": 120,
            },
            {
                "label": _("Cost Center"),
                "fieldname": "cost_center",
                "fieldtype": "Link",
                "options": "Cost Center",
                "width": 100,
            },
            {
                "label": _("Workshop Division"),
                "fieldname": "vehicle_workshop_division",
                "fieldtype": "Link",
                "options": "Vehicle Workshop",
                "width": 100,
            },
            {
                "label": _("Service Advisor"),
                "fieldname": "service_advisor",
                "fieldtype": "Link",
                "options": "Sales Person",
                "width": 150,
            },
            {
                "label": _("Customer Group"),
                "fieldname": "customer_group",
                "fieldtype": "Link",
                "options": "Customer Group",
                "width": 120,
            },
        ]

        if len(self.group_by) <= 1:
            columns = [c for c in columns if c.get("fieldname") not in ("reference_type", "reference")]
        else:
            columns = [c for c in columns if c.get("fieldname") != "project"]
            if self.filters.totals_only:
                columns = [
                    c
                    for c in columns
                    if c.get("fieldname")
                    not in (
                        "final_invoice_date",
                        "project",
                        "sales_invoice",
                        "vehicle_workshop",
                        "branch",
                        "vehicle_workshop_division",
                        "cost_center",
                        "service_advisor",
                        "customer_group",
                    )
                ]

        return columns
