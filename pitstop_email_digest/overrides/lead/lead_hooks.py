from ...utils.send_data_vendor.send_data_genesys import send_data_genesys


def after_insert(doc, method=None):
    send_data_genesys(doc)
