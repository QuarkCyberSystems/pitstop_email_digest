from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def notify_service_maintenance_contract_expire(doc, handler=None):
    extra_key_args = {}
    if not doc.contact_mobile and doc.contact_phone:
        extra_key_args = {"contact_mobile": doc.contact_phone}
    send_data_genesys(doc, extra_key_args=extra_key_args)
