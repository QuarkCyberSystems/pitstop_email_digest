import json

import frappe
from frappe.utils import evaluate_filters


def send_data_genesys(doc, campaing_name=None, extra_key_args=None):
    settings = frappe.get_single("Genesys Settings")

    if not settings.enable or frappe.conf.developer_mode:
        return

    campaign = settings.get_campaign_details(doc, campaing_name)

    if campaign:
        send_campaign = True
        if campaign[0].filters:
            fitlers_dict = json.loads(campaign[0].filters)
            send_campaign = evaluate_filters(doc, fitlers_dict)
        if send_campaign:
            settings.send_campaign(campaign, doc, extra_key_args)
