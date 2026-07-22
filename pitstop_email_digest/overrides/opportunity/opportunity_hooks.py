from twilio_integration.overrides.notification_hooks import format_numbers_for_whatsapp

from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def notify_recall_lost_opportunity(doc, method=None):
    extra_key_args = {}

    if doc.contact_mobile:
        extra_key_args["contact_mobile"] = (
            format_numbers_for_whatsapp([doc.contact_mobile])[0]
            if format_numbers_for_whatsapp([doc.contact_mobile])
            else None
        )

    if not doc.contact_mobile and doc.contact_phone:
        extra_key_args["contact_mobile"] = (
            format_numbers_for_whatsapp([doc.contact_phone])[0]
            if format_numbers_for_whatsapp([doc.contact_phone])
            else None
        )

    send_data_genesys(doc, extra_key_args=extra_key_args)
