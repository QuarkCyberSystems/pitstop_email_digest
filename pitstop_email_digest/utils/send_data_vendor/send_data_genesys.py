import frappe


def send_data_genesys(doc, campaing_name=None, extra_key_args=None):
    settings = frappe.get_single("Genesys Settings")

    if not settings.enable:
        return

    campaign = settings.get_campaign_details(doc, campaing_name)

    if campaign:
        settings.send_campaign(campaign, doc, extra_key_args)
