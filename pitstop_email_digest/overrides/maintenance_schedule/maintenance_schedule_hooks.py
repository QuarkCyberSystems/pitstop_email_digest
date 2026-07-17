import frappe

from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def notify_maintenance_opportunity(doc, handler=None, context=None):
    extra_key_args = {}
    if context:
        if (
            context.get("row")
            and context.get("row").get("reference_doctype")
            and context.get("row").get("reference_name")
        ):
            ro_doc = frappe.get_doc(
                context.get("row").get("reference_doctype"),
                context.get("row").get("reference_name"),
            )
            extra_key_args["vehicle_license_plate"] = ro_doc.get(
                "vehicle_license_plate"
            )
            extra_key_args["vehicle_chassis_no"] = ro_doc.get("vehicle_chassis_no")
            extra_key_args["branch"] = ro_doc.get("branch")

    if not doc.contact_phone and doc.contact_mobile:
        extra_key_args["contact_phone"] = doc.contact_mobile
    send_data_genesys(doc, extra_key_args=extra_key_args)
