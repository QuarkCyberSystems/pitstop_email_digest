# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import json

import frappe
import requests
from frappe.model.document import Document


class GenesysSettings(Document):
    # pitstop_email_digest/integrations/vendor_api.py
    def get_access_token(self):
        CACHE_KEY = self.genesys_oauth_cache_key
        cached = frappe.cache().get_value(CACHE_KEY)
        if cached:
            return cached

        client_secret = self.get_password("client_secret")

        resp = requests.post(
            self.token_url,
            data={"grant_type": self.grant_type},
            auth=(self.client_id, client_secret),  # Basic Auth
            timeout=10,
        )

        resp.raise_for_status()
        token_data = resp.json()

        access_token = token_data["access_token"]
        expires_in = token_data.get("expires_in", 3600)

        # cache with a small buffer so we refresh before actual expiry
        frappe.cache().set_value(
            CACHE_KEY, access_token, expires_in_sec=expires_in - 1500
        )

        return access_token

    def create_genesys_log(
        self,
        reference_doctype,
        reference_name,
        payload,
        status,
        campaign_name,
        campaign_url,
        trace_back=None,
    ):
        gl = frappe.new_doc("Genesys Log")
        gl.reference_doctype = reference_doctype
        gl.reference_name = reference_name
        gl.status = status
        gl.campaign_name = campaign_name
        gl.campaign_url = campaign_url
        gl.payload = json.dumps(payload, indent=4, default=str)
        if trace_back:
            gl.trace_back = trace_back
        gl.flags.ignore_permissions = True
        gl.save()

    def send_to_genesys(
        self, url, payload, reference_doctype, reference_name, campaign_name
    ):
        try:
            token = self.get_access_token()
        except requests.RequestException as e:
            frappe.log_error(
                message=frappe.get_traceback() + str(e),
                title="Genesys OAuth token fetch failed",
            )
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            url,
            data=frappe.as_json([{"data": payload}]),
            headers=headers,
            timeout=15,
        )

        # if token expired mid-flight, refresh once and retry
        if resp.status_code == 401:
            frappe.cache().delete_value(self.genesys_oauth_cache_key)
            token = self.get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            resp = requests.post(
                url,
                data=frappe.as_json([{"data": payload}]),
                headers=headers,
                timeout=15,
            )

        if not resp.ok:
            self.create_genesys_log(
                reference_doctype=reference_doctype,
                reference_name=reference_name,
                payload=[{"data": payload}],
                status="Failed",
                campaign_url=url,
                campaign_name=campaign_name,
                trace_back=resp.text,
            )
        else:
            self.create_genesys_log(
                reference_doctype=reference_doctype,
                reference_name=reference_name,
                payload=[{"data": payload}],
                status="Success",
                campaign_url=url,
                campaign_name=campaign_name,
            )

    def get_campaign_details(self, doc, campaign_name=None):
        filters = {
            "parent": "Genesys Settings",
            "parentfield": "campaign_details",
            "campaign_doctype": doc.doctype,
        }

        if campaign_name:
            filters["campaign_name"] = campaign_name

        campaign = frappe.get_all(
            "Campaign Details",
            filters=filters,
            fields=["campaign_url", "field_map", "campaign_name"],
            limit_page_length=1,
        )
        return campaign

    def build_payload(self, doc, field_map=None, extra_key_args=None):
        field_map = field_map or {}
        doc_dict = doc.as_dict()
        if extra_key_args:
            doc_dict.update(extra_key_args)
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

    def send_campaign(self, campaign, doc, extra_key_args=None):
        campaign_url = campaign[0].campaign_url
        field_map = campaign[0].field_map
        campaign_name = campaign[0].campaign_name
        field_map = json.loads(field_map) if field_map else {}
        if campaign_url:
            payload = self.build_payload(
                doc=doc, field_map=field_map, extra_key_args=extra_key_args
            )
            frappe.enqueue_doc(
                "Genesys Settings",
                "Genesys Settings",
                "send_to_genesys",
                queue="short",
                url=campaign_url,
                payload=payload,
                reference_doctype=doc.doctype,
                reference_name=doc.name,
                campaign_name=campaign_name,
                enqueue_after_commit=True,
            )
