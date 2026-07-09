import frappe


def after_insert(doc, method=None):
    settings = frappe.get_single("Genesis Settings")

    if not settings.enable:
        return

    campaign = settings.get_campaign_details(doc)

    if campaign:
        settings.send_campaign(campaign, doc)
