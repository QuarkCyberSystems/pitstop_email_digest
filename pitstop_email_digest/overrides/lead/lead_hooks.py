from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def after_insert(doc, method=None):
    extra_key_args = {}
    extra_key_args["customerid"] = doc.name
    send_data_genesys(doc, extra_key_args=extra_key_args)
