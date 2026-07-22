from twilio_integration.overrides.notification_hooks import format_numbers_for_whatsapp

from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def after_insert(doc, method=None):
    extra_key_args = {}
    extra_key_args["customerid"] = doc.name
    if doc.mobile_no:
        extra_key_args["mobile_no"] = (
            format_numbers_for_whatsapp([doc.mobile_no])[0]
            if format_numbers_for_whatsapp([doc.mobile_no])
            else None
        )
    send_data_genesys(doc, extra_key_args=extra_key_args)
