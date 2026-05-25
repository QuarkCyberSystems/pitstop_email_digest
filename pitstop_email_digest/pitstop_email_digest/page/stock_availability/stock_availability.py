import frappe
from erpnext.stock.report.stock_balance.stock_balance import StockBalanceReport

from pitstop_email_digest.overrides.sle.sle_items import get_items_from_voucher


@frappe.whitelist()
def get_items_balance(voucher_type, voucher_no, from_date, to_date):
    filters = {
        "voucher_type": voucher_type,
        "voucher_no": voucher_no,
        "from_date": from_date,
        "to_date": to_date,
    }
    columns, rows = StockBalanceReport(filters).run()
    items_dict = get_items_from_voucher(voucher_type, voucher_no, item_name=True)
    return {"columns": columns, "rows": rows, "items_dict": items_dict}


@frappe.whitelist()
def get_items_stock_transaction(voucher_type, voucher_no, from_date, to_date):
    items_dict = get_items_from_voucher(voucher_type, voucher_no, item_name=True)
    if not items_dict:
        return {"rows": []}

    rows = []
    for item_code_dict in items_dict:
        last_in = frappe.db.get_value(
            "Stock Ledger Entry",
            {
                "item_code": item_code_dict.get("item_code"),
                "actual_qty": [">", 0],
                "is_cancelled": 0,
            },
            "warehouse",
            order_by="posting_date desc, posting_time desc, creation desc",
        )
        last_out = frappe.db.get_value(
            "Stock Ledger Entry",
            {
                "item_code": item_code_dict.get("item_code"),
                "actual_qty": ["<", 0],
                "is_cancelled": 0,
            },
            "warehouse",
            order_by="posting_date desc, posting_time desc, creation desc",
        )
        rows.append(
            {
                "item_code": item_code_dict.get("item_code"),
                "item_name": item_code_dict.get("item_name") or "",
                "last_in_warehouse": last_in or "",
                "last_out_warehouse": last_out or "",
            }
        )

    return {"rows": rows}
