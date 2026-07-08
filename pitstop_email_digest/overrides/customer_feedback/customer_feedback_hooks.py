import json

import frappe


def after_insert(doc, method=None):
    settings = frappe.get_single("Genesis Settings")

    campaign = frappe.get_all(
        "Campaign Details",
        filters={
            "parent": "Genesis Settings",
            "parentfield": "campaign_details",
            "campaign_doctype": doc.doctype,
        },
        fields=["campaign_url", "field_map", "campaign_name"],
        limit_page_length=1,
    )

    if campaign:
        campaign_url = campaign[0].campaign_url
        field_map = campaign[0].field_map
        campaign_name = campaign[0].campaign_name
        field_map = json.loads(field_map) if field_map else {}
        if campaign_url:
            payload = build_cfb_payload(doc, field_map)
            settings.send_quotation_to_vendor(
                url=campaign_url,
                payload=payload,
                reference_doctype=doc.doctype,
                reference_name=doc.name,
                campaign_name=campaign_name,
            )
    return campaign


def build_cfb_payload(doc, field_map=None):
    field_map = field_map or {}
    doc_dict = doc.as_dict()
    updated_dict = {}
    free_counter = 0

    for each_key, mapped_key in field_map.items():
        updated_dict[mapped_key] = doc_dict.get(each_key) or "N/A"

    for each_key, value in doc_dict.items():
        if each_key not in field_map:
            free_counter += 1
            updated_dict[f"free{free_counter}"] = value or "N/A"
            # Contact lists do not support more than 10 extra data columns.
            if free_counter >= 10:
                break

    return updated_dict
