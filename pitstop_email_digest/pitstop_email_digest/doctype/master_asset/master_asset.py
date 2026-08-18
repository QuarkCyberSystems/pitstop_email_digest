import frappe
from frappe.model.document import Document


class MasterAsset(Document):
    def validate(self):
        self.validate_purchase_order_required()
        self.validate_purchase_order_submitted()
        self.validate_purchase_order_uniqueness()

    def validate_purchase_order_required(self):
        if self.source_type == "From Purchase Order" and not self.purchase_order:
            frappe.throw(
                frappe._("Purchase Order is required when Source is {0}").format(
                    frappe.bold(frappe._("From Purchase Order"))
                )
            )

    def validate_purchase_order_submitted(self):
        if not self.purchase_order:
            return
        docstatus = frappe.db.get_value(
            "Purchase Order", self.purchase_order, "docstatus"
        )
        if docstatus != 1:
            frappe.throw(
                frappe._(
                    "Purchase Order {0} must be submitted before it can be linked to a Master Asset."
                ).format(frappe.bold(self.purchase_order))
            )

    def before_save(self):
        self.recompute_summary()

    def onload(self):
        self.set_onload("linked_assets", self.get_linked_assets())

    def validate_purchase_order_uniqueness(self):
        if not self.purchase_order:
            return
        existing = frappe.db.get_value(
            "Master Asset",
            {"purchase_order": self.purchase_order, "name": ("!=", self.name)},
            "name",
        )
        if existing:
            frappe.throw(
                frappe._(
                    "Master Asset {0} already exists for Purchase Order {1}"
                ).format(frappe.bold(existing), frappe.bold(self.purchase_order))
            )

    def get_linked_assets(self):
        return frappe.get_all(
            "Asset",
            filters={"master_asset": self.name, "docstatus": ("<", 2)},
            fields=[
                "name",
                "asset_name",
                "item_code",
                "status",
                "gross_purchase_amount",
                "purchase_date",
                "location",
            ],
            order_by="creation asc",
        )

    def recompute_summary(self):
        rows = frappe.db.sql(
            """
			select count(name) as cnt, coalesce(sum(gross_purchase_amount), 0) as val
			from `tabAsset`
			where master_asset = %s and docstatus < 2
			""",
            self.name,
            as_dict=True,
        )
        row = rows[0] if rows else {"cnt": 0, "val": 0}
        self.total_assets = row.cnt or 0
        self.total_asset_value = row.val or 0

    def refresh_summary_and_save(self):
        self.recompute_summary()
        self.db_set(
            {
                "total_assets": self.total_assets,
                "total_asset_value": self.total_asset_value,
            },
            update_modified=False,
        )
