from twilio_integration.overrides.notification_hooks import format_numbers_for_whatsapp

from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def notify_appointment_missed(doc, handler=None):
    extra_key_args = {}
    if doc.contact_mobile:
        extra_key_args["contact_mobile"] = (
            format_numbers_for_whatsapp([doc.contact_mobile])[0]
            if format_numbers_for_whatsapp([doc.contact_mobile])
            else None
        )
    send_data_genesys(
        doc, campaing_name="Pitstop No Show Reminder", extra_key_args=extra_key_args
    )


def notify_appointment_reminder(doc, handler=None):
    extra_key_args = {}
    if doc.contact_mobile:
        extra_key_args["contact_mobile"] = (
            format_numbers_for_whatsapp([doc.contact_mobile])[0]
            if format_numbers_for_whatsapp([doc.contact_mobile])
            else None
        )
    send_data_genesys(
        doc,
        campaing_name="Pitstop Service / Appointment Reminder",
        extra_key_args=extra_key_args,
    )
