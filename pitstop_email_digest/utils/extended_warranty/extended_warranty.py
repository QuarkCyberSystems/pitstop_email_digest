import frappe
from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
    get_accounting_dimensions,
)


def set_extended_warranty_check(self):
    WARRANTY_FIELDS = [
        ("unearned_revenue_percentage", "Unearned Revenue Percentage"),
        ("extended_warranty_cos", "Extended Warranty COS"),
        ("extended_warranty_liability", "Extended Warranty Liability"),
        ("extended_warranty_supplier", "Extended Warranty Supplier"),
    ]

    for row in self.items:
        config = check_item_code_extend_warranty_config(
            row.item_code, row.extended_warranty_supplier
        )
        row.is_extended_warranty = config["is_extended_warranty"]

        if not config["is_extended_warranty"]:
            # Clear all warranty fields
            row.unearned_revenue_percentage = 0.0
            row.extended_warranty_cos = None
            row.extended_warranty_liability = None
            row.extended_warranty_supplier = None
            row.extended_warranty_supplier_name = None
            continue

        if config.get("force"):
            # Auto-fill from config
            row.unearned_revenue_percentage = config.get(
                "unearned_revenue_percentage", 0.0
            )
            row.extended_warranty_cos = config.get("extended_warranty_cos")
            row.extended_warranty_liability = config.get("extended_warranty_liability")
            row.extended_warranty_supplier = config.get("extended_warranty_supplier")
            row.extended_warranty_supplier_name = config.get(
                "extended_warranty_supplier_name"
            )
            continue

        # Validate mandatory fields are filled
        missing_fields = [
            label for field, label in WARRANTY_FIELDS if not row.get(field)
        ]

        if missing_fields:
            frappe.throw(
                "The following fields are mandatory for extended warranty item "
                "<b>{0}</b> (Row #{1}):<br><ul>{2}</ul>".format(
                    row.item_code,
                    row.idx,
                    "".join(f"<li>{field}</li>" for field in missing_fields),
                )
            )


def create_extended_warranty_jv(self):
    extended_warranty_rows = [row for row in self.items if row.is_extended_warranty]
    if not extended_warranty_rows:
        return

    jv = frappe.new_doc("Journal Entry")
    jv.voucher_type = "Journal Entry"
    jv.posting_date = self.posting_date
    jv.company = self.company
    jv.user_remark = f"Extended Warranty JV for Sales Invoice {self.name}"
    jv.branch = self.branch
    jv.cost_center = self.cost_center
    jv.project = self.project
    jv.extended_warranty_voucher = self.name

    # Fetch remark template and submit_je flag from Extended Warranty Configure settings
    remark_template, submit_je = frappe.get_cached_value(
        "Extended Warranty Configure",
        "Extended Warranty Configure",  # single doctype
        ["user_remark", "submit_je"],
    )

    remark_template = remark_template or "Extended Warranty JV for Sales Invoice {name}"

    # Format the remark template with invoice fields
    try:
        user_remark = remark_template.format(
            name=self.name,
            customer=self.bill_to,
            customer_name=self.bill_to_name,
            posting_date=self.posting_date,
            company=self.company,
        )
    except KeyError as e:
        frappe.log_error(
            f"Invalid placeholder {e} in Extended Warranty user_remark template",
            "Extended Warranty JV",
        )
        user_remark = f"Extended Warranty JV for Sales Invoice {self.name}"

    jv.user_remark = user_remark

    for row in extended_warranty_rows:
        amount = (row.unearned_revenue_percentage / 100) * row.base_net_amount

        # Build dimension dict — row level first, fallback to invoice level
        dimensions = {}
        accounting_dimensions = get_accounting_dimensions()
        for dimension_field in accounting_dimensions:
            value = row.get(dimension_field) or self.get(dimension_field)
            if value:
                dimensions[dimension_field] = value

        base_account_entry = {**dimensions}

        # Debit — Extended Warranty COS
        jv.append(
            "accounts",
            {
                **base_account_entry,
                "account": row.extended_warranty_cos,
                "debit_in_account_currency": amount,
                "credit_in_account_currency": 0.0,
            },
        )

        # Credit — Extended Warranty Liability
        jv.append(
            "accounts",
            {
                **base_account_entry,
                "account": row.extended_warranty_liability,
                "debit_in_account_currency": 0.0,
                "credit_in_account_currency": amount,
            },
        )

    jv.insert(ignore_permissions=True)
    # Draft mode — do NOT call jv.submit()
    # Submit or keep draft based on Extended Warranty Configure setting
    if submit_je:
        jv.submit()
        status = "Submitted"
    else:
        status = "Draft"

    frappe.msgprint(
        f"Extended Warranty Journal Entry <b>{jv.name}</b> created in {status}.",
        indicator="green",
        alert=True,
    )


@frappe.whitelist()
def get_extended_warranty_item_details(item_code, supplier=None):
    if item_code:
        return check_item_code_extend_warranty_config(item_code, supplier)


def check_item_code_extend_warranty_config(item_code, supplier=None):
    result_dict = {
        "is_extended_warranty": False,
        "unearned_revenue_percentage": 0.0,
        "extended_warranty_cos": None,
        "extended_warranty_liability": None,
        "extended_warranty_supplier": None,
        "extended_warranty_supplier_name": None,
    }

    if not frappe.get_cached_value("Item", item_code, "is_extended_warranty"):
        return result_dict

    config = frappe.get_all(
        "Extended Warranty Configure Details",
        filters=get_filters(item_code, supplier),
        fields=[
            "unearned_revenue_percentage",
            "extended_warranty_cos",
            "extended_warranty_liability",
            "extended_warranty_supplier",
            "extended_warranty_supplier_name",
            "force",
        ],
    )

    if config:
        result_dict["is_extended_warranty"] = True
        row = config[0]
        result_dict.update(
            {
                "unearned_revenue_percentage": row.get("unearned_revenue_percentage")
                or 0.0,
                "extended_warranty_cos": row.get("extended_warranty_cos"),
                "extended_warranty_liability": row.get("extended_warranty_liability"),
                "extended_warranty_supplier": row.get("extended_warranty_supplier"),
                "extended_warranty_supplier_name": row.get(
                    "extended_warranty_supplier_name"
                ),
                "force": row.get("force"),
            }
        )

    return result_dict


def get_filters(item_code, supplier=None):
    filters = {
        "warranty_item": item_code,
        "default": 1,
        "parent": "Extended Warranty Configure",
        "parentfield": "extended_warranty_configure_details",
    }
    if supplier:
        del filters["default"]
        filters["extended_warranty_supplier"] = supplier
    return filters
