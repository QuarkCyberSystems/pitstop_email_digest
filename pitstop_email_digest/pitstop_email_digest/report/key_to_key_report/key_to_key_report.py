# Copyright (c) 2025, QCS and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _
from frappe.utils import (
    format_datetime,
    format_time,
    formatdate,
    get_time,
    getdate,
    now_datetime,
)

date_format = "dd/MM/y"
time_format = "hh:mm a"
datetime_format = "{0}, {1}".format(date_format, time_format)


class VehicleKeyToKeyReport(object):
    def __init__(self, filters=None):
        self.filters = frappe._dict(filters or {})
        self.filters.to_date = getdate(self.filters.to_date)

        self.report_date = getdate(self.filters.to_date)
        self.report_time = get_time(now_datetime()) if self.report_date == getdate() else datetime.time.max
        self.report_dt = frappe.utils.combine_datetime(self.report_date, self.report_time)

        if getdate(self.filters.from_date) > self.filters.to_date:
            frappe.throw(_("From Date cannot be after To Date"))

    def run(self):
        self.get_data()
        self.process_data()
        columns = self.get_columns()

        return columns, self.data

    def get_conditions(self):
        conditions = ""

        if self.filters.to_date:
            conditions += " and p.vehicle_received_date <= '{to_date}'".format(to_date=self.filters.get("to_date"))

        if self.filters.from_date:
            conditions += " and p.vehicle_received_date >= '{from_date}'".format(from_date=self.filters.get("from_date"))

        if self.filters.workshop_division:
            conditions += " and p.vehicle_workshop_division = '{vehicle_workshop_division}'".format(vehicle_workshop_division=self.filters.workshop_division)

        if self.filters.repair_order:
            conditions += " and p.name = '{repair_order}'".format(repair_order=self.filters.repair_order)

        return conditions

    def get_data(self):
        conditions = self.get_conditions()

        self.data = frappe.db.sql(
            """
			select p.name as project, p.project_name, p.project_type, p.project_date,
				p.vehicle_workshop, p.vehicle_workshop_division, p.company,
				p.project_status, p.procurement_status, p.delivery_status,
				p.customer, p.customer_group,
				p.customer_name, p.bill_to, p.bill_to_name,
				p.contact_mobile, p.contact_mobile_2, p.contact_phone,
				p.applies_to_vehicle, p.service_advisor, p.service_manager,
				p.applies_to_item, p.applies_to_item_name, p.applies_to_variant_of, p.applies_to_variant_of_name,
				p.vehicle_license_plate, p.vehicle_chassis_no, p.vehicle_engine_no, p.vehicle_unregistered, p.vehicle_color,
				p.vehicle_received_date, p.vehicle_received_time,
				p.last_purchase_order_date, p.last_purchase_receipt_date, p.last_material_request_date, p.pending_quotation_amount,
				timestamp(p.vehicle_received_date, p.vehicle_received_time) as vehicle_received_dt,
				p.vehicle_delivered_date, p.vehicle_delivered_time,
				timestamp(p.vehicle_delivered_date, p.vehicle_delivered_time) as vehicle_delivered_dt,
				p.expected_delivery_date, p.expected_delivery_time,
				timestamp(p.expected_delivery_date, p.expected_delivery_time) as expected_delivery_dt,
				p.ready_to_close, p.ready_to_close_dt,
				date(p.ready_to_close_dt) as ready_to_close_date, time(p.ready_to_close_dt) as ready_to_close_time,
				p.billing_status, p.customer_billable_amount, p.total_billable_amount,
				p.final_invoice_date, p.creation, p.insurance_loss_no, sii.posting_date
			from `tabProject` p
			-- Latest Vehicle Service Receipt per project
			JOIN (
				SELECT t1.*
				FROM `tabVehicle Service Receipt` t1
				JOIN (
					SELECT project, MAX(creation) AS max_creation
					FROM `tabVehicle Service Receipt`
					WHERE docstatus = 1
					GROUP BY project
				) t2 ON t1.project = t2.project AND t1.creation = t2.max_creation
				WHERE t1.docstatus = 1
			) tvsr ON tvsr.project = p.name

			-- Latest Vehicle Gate Pass per project
			LEFT JOIN (
				SELECT t1.*
				FROM `tabVehicle Gate Pass` t1
				JOIN (
					SELECT project, MAX(creation) AS max_creation
					FROM `tabVehicle Gate Pass`
					WHERE docstatus = 1
					GROUP BY project
				) t2 ON t1.project = t2.project AND t1.creation = t2.max_creation
				WHERE t1.docstatus = 1
			) tvgp ON tvgp.project = p.name

			-- First Sales Invoice Item per project (based on parent invoice's creation)
			LEFT JOIN (
				SELECT sii.*, si.posting_date
				FROM `tabSales Invoice Item` sii
				JOIN `tabSales Invoice` si ON si.name = sii.parent

				-- Match invoice with the earliest posting_date + name per project
				JOIN (
					SELECT
						sii_inner.project,
						MIN(CONCAT(si_inner.posting_date, '-', si_inner.name)) AS min_posting_key
					FROM `tabSales Invoice Item` sii_inner
					JOIN `tabSales Invoice` si_inner ON si_inner.name = sii_inner.parent
					WHERE si_inner.docstatus = 1
					GROUP BY sii_inner.project
				) first_invoice
				ON sii.project = first_invoice.project
				JOIN `tabSales Invoice` si2 ON si2.name = sii.parent
				AND CONCAT(si2.posting_date, '-', si2.name) = first_invoice.min_posting_key

				WHERE sii.idx = 1 AND si.docstatus = 1
			) sii ON sii.project = p.name

			left join `tabItem` item on item.name = p.applies_to_item
			where status != 'Cancelled' {0}
			order by p.vehicle_received_date, p.vehicle_received_time, p.project_date
		""".format(conditions),
            as_dict=1,
        )

        return self.data

    def get_columns(self):
        columns = [
            {
                "label": _("Vehicle"),
                "fieldname": "applies_to_vehicle",
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "label": _("Customer"),
                "fieldname": "customer",
                "fieldtype": "Link",
                "options": "Customer",
                "width": 80,
            },
            {
                "label": _("Customer Name"),
                "fieldname": "customer_name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Customer Group"),
                "fieldname": "customer_group",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Vehicle Received Date/Time"),
                "fieldname": "vehicle_received_dt_fmt",
                "fieldtype": "Data",
                "width": 160,
            },
            {
                "label": _("Delivered Date/Time"),
                "fieldname": "vehicle_delivered_dt_fmt",
                "fieldtype": "Data",
                "width": 140,
            },
            {
                "label": _("Duration/ Key to Key (Days)"),
                "fieldname": "age",
                "fieldtype": "Int",
                "width": 150,
            },
            {
                "label": _("Vehicle Ready for collection Date/Time"),
                "fieldname": "ready_to_close_dt_fmt",
                "fieldtype": "Data",
                "width": 160,
            },
            {
                "label": _("Promised Date/Time"),
                "fieldname": "expected_delivery_dt_fmt",
                "fieldtype": "Data",
                "width": 140,
            },
            {
                "label": _("Project"),
                "fieldname": "project",
                "fieldtype": "Link",
                "options": "Project",
                "width": 130,
                "report_time": self.report_time,
                "report_time_fmt": format_time(self.report_time, time_format),
            },
            {
                "label": _("Job Date"),
                "fieldname": "project_date",
                "fieldtype": "Date",
                "width": 80,
            },
            {
                "label": _("Ready"),
                "fieldname": "ready_to_close",
                "fieldtype": "Check",
                "width": 50,
            },
            {
                "label": _("Billed"),
                "fieldname": "billed",
                "fieldtype": "Check",
                "width": 50,
            },
            {
                "label": _("Delivered"),
                "fieldname": "delivered",
                "fieldtype": "Check",
                "width": 55,
            },
            {
                "label": _("Workshop"),
                "fieldname": "vehicle_workshop",
                "fieldtype": "Link",
                "options": "Vehicle Workshop",
                "width": 120,
            },
            {
                "label": _("Workshop Division"),
                "fieldname": "vehicle_workshop_division",
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "label": _("Model"),
                "fieldname": "applies_to_variant_of_name",
                "fieldtype": "Data",
                "width": 120,
            },
            {
                "label": _("Variant Code"),
                "fieldname": "applies_to_item",
                "fieldtype": "Link",
                "options": "Item",
                "width": 120,
            },
            {
                "label": _("Reg No"),
                "fieldname": "vehicle_license_plate",
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "label": _("Chassis No"),
                "fieldname": "vehicle_chassis_no",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Service Advisor"),
                "fieldname": "service_advisor",
                "fieldtype": "Link",
                "options": "Sales Person",
                "width": 120,
            },
            {
                "label": _("Customer Comments"),
                "fieldname": "project_name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Bill To"),
                "fieldname": "bill_to",
                "fieldtype": "Link",
                "options": "Customer",
                "width": 80,
            },
            {
                "label": _("Bill To Name"),
                "fieldname": "bill_to_name",
                "fieldtype": "Data",
                "width": 150,
            },
            {
                "label": _("Contact #"),
                "fieldname": "contact_no",
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "label": _("Job Status"),
                "fieldname": "project_status",
                "fieldtype": "Data",
                "width": 110,
            },
            {
                "label": _("Material Status"),
                "fieldname": "delivery_status",
                "fieldtype": "Data",
                "width": 110,
            },
            {
                "label": _("Procurement Status"),
                "fieldname": "procurement_status",
                "fieldtype": "Data",
                "width": 100,
            },
            {
                "label": _("Billable Amount"),
                "fieldname": "total_billable_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Pending Quotation Amount"),
                "fieldname": "pending_quotation_amount",
                "fieldtype": "Currency",
                "options": "Company:company:default_currency",
                "width": 100,
            },
            {
                "label": _("Ready Date/Time"),
                "fieldname": "ready_to_close_dt_fmt",
                "fieldtype": "Data",
                "width": 140,
            },
            {
                "label": _("Ready in Days"),
                "fieldname": "ready_days",
                "fieldtype": "int",
                "width": 75,
            },
            {
                "label": _("Final Invoice Date"),
                "fieldname": "final_invoice_date_fmt",
                "fieldtype": "Data",
                "width": 90,
            },
            {
                "label": _("Invoiced in Days"),
                "fieldname": "invoiced_days",
                "fieldtype": "int",
                "width": 75,
            },
            {
                "label": _("Last MR Date"),
                "fieldname": "last_material_request_date",
                "fieldtype": "Date",
                "width": 90,
            },
            {
                "label": _("Last PO Date"),
                "fieldname": "last_purchase_order_date",
                "fieldtype": "Date",
                "width": 90,
            },
            {
                "label": _("Last PR Date"),
                "fieldname": "last_purchase_receipt_date",
                "fieldtype": "Date",
                "width": 90,
            },
            {
                "label": _("Created On"),
                "fieldname": "creation_dt_fmt",
                "fieldtype": "Data",
                "width": 90,
            },
            {
                "label": _("RO to Invoice Days"),
                "fieldname": "ro_to_invoice",
                "fieldtype": "Data",
                "width": 90,
            },
        ]

        if self.filters.get("workshop_division") == "Bodyshop":
            columns.extend(
                [
                    {
                        "label": _("Insurance Claim #"),
                        "fieldname": "insurance_loss_no",
                        "fieldtype": "Data",
                        "width": 130,
                    },
                ]
            )

        return columns

    def process_data(self):
        for d in self.data:
            # Status
            d.delivered = 1 if d.vehicle_delivered_date else 0
            d.billed = 0 if d.billing_status in ["Not Applicable", "Not Billed"] else 1

            # Date/Time Formatting
            self.set_formatted_datetime(d)

            # Model Name if not a variant
            if not d.applies_to_variant_of_name:
                d.applies_to_variant_of_name = d.applies_to_item_name

            # Unregistered
            if not d.vehicle_license_plate and d.vehicle_unregistered:
                d.vehicle_license_plate = _("Unreg")

            # Contact No
            d.contact_no = d.contact_mobile or d.contact_mobile_2 or d.contact_phone

            # Age
            start_date = d.vehicle_received_date
            if start_date:
                start_date = getdate(start_date)

                if start_date and d.vehicle_delivered_date:
                    d.age = (getdate(d.vehicle_delivered_date) - start_date).days or 0

                if d.ready_to_close_dt:
                    d.ready_days = (getdate(d.ready_to_close_dt) - start_date).days

                if d.final_invoice_date:
                    d.invoiced_days = (getdate(d.final_invoice_date) - start_date).days

                if d.posting_date:
                    d.ro_to_invoice = (getdate(d.posting_date) - start_date).days

            # Is Late
            # self.set_late_or_early(d)

    def set_formatted_datetime(self, d):
        d.vehicle_received_date_fmt = formatdate(d.vehicle_received_dt, date_format)
        d.vehicle_received_time_fmt = format_time(d.vehicle_received_dt, time_format)
        d.vehicle_received_dt_fmt = format_datetime(d.vehicle_received_dt, datetime_format)

        d.vehicle_delivered_dt_fmt = format_datetime(d.vehicle_delivered_dt, datetime_format)

        d.ready_to_close_date_fmt = formatdate(d.ready_to_close_dt, date_format)
        d.ready_to_close_time_fmt = format_time(d.ready_to_close_dt, time_format)
        d.ready_to_close_dt_fmt = format_datetime(d.ready_to_close_dt, datetime_format)

        d.expected_delivery_date_fmt = formatdate(d.expected_delivery_date, date_format)
        d.expected_delivery_time_fmt = format_time(d.expected_delivery_time, time_format)

        d.final_invoice_date_fmt = formatdate(d.final_invoice_date, date_format)
        d.creation_dt_fmt = format_datetime(d.creation, datetime_format)

        if d.expected_delivery_date and d.expected_delivery_time:
            d.expected_delivery_dt_fmt = format_datetime(d.expected_delivery_dt, datetime_format)
        elif d.expected_delivery_date:
            d.expected_delivery_dt_fmt = formatdate(d.expected_delivery_date, date_format)


def execute(filters=None):
    return VehicleKeyToKeyReport(filters).run()
