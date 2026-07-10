import frappe

from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def notify_maintenance_remainder_in_advance(doc, handler=None, scheduler_doc=None):
    extra_key_args = {}
    if scheduler_doc:
        if scheduler_doc.get("reference_doctype") and scheduler_doc.get(
            "reference_name"
        ):
            ro_doc = frappe.get_doc(
                scheduler_doc.get("reference_doctype"),
                scheduler_doc.get("reference_name"),
            )
            extra_key_args["vehicle_license_plate"] = ro_doc.get(
                "vehicle_license_plate"
            )
            extra_key_args["vehicle_chassis_no"] = ro_doc.get("vehicle_chassis_no")
            extra_key_args["branch"] = ro_doc.get("branch")
    send_data_genesys(doc, extra_key_args=extra_key_args)
