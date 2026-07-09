# Copyright (c) 2026, QCS and contributors
# For license information, please see license.txt

import json

import frappe
import requests
from frappe.model.document import Document


class GenesisSettings(Document):
    # pitstop_email_digest/integrations/vendor_api.py
    def get_access_token(self):
        CACHE_KEY = self.genesis_oauth_cache_key
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

    def create_genesis_log(
        self,
        reference_doctype,
        reference_name,
        payload,
        status,
        campaign_name,
        campaign_url,
        trace_back=None,
    ):
        gl = frappe.new_doc("Genesis Log")
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

    def send_to_genesis(
        self, url, payload, reference_doctype, reference_name, campaign_name
    ):
        try:
            token = self.get_access_token()
        except requests.RequestException as e:
            frappe.log_error(
                message=frappe.get_traceback() + str(e),
                title="Genesis OAuth token fetch failed",
            )
            return

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        resp = requests.post(
            url,
            data=json.dumps([{"data": payload}]),
            headers=headers,
            timeout=15,
        )

        # if token expired mid-flight, refresh once and retry
        if resp.status_code == 401:
            frappe.cache().delete_value(self.genesis_oauth_cache_key)
            token = self.get_access_token()
            headers["Authorization"] = f"Bearer {token}"
            resp = requests.post(
                url,
                data=json.dumps([{"data": payload}]),
                headers=headers,
                timeout=15,
            )

        if not resp.ok:
            self.create_genesis_log(
                reference_doctype=reference_doctype,
                reference_name=reference_name,
                payload=[{"data": payload}],
                status="Failed",
                campaign_url=url,
                campaign_name=campaign_name,
                trace_back=resp.text,
            )
        else:
            self.create_genesis_log(
                reference_doctype=reference_doctype,
                reference_name=reference_name,
                payload=[{"data": payload}],
                status="Success",
                campaign_url=url,
                campaign_name=campaign_name,
            )
