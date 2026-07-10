from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def notify_appointment_missed(doc, handler=None):
    send_data_genesys(doc, campaing_name="Pitstop No Show Reminder")


def notify_appointment_reminder(doc, handler=None):
    send_data_genesys(doc, campaing_name="Pitstop Service / Appointment Reminder")
