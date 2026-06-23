from automotive.overrides.sales_invoice.sales_invoice_hooks import SalesInvoiceAuto

from ...utils.extended_warranty.extended_warranty import (
    create_extended_warranty_jv,
    set_extended_warranty_check,
)


class SalesInvoicePitstopEmailDigest(SalesInvoiceAuto):
    def validate(self):
        super().validate()
        set_extended_warranty_check(self)

    def on_submit(self):
        super().on_submit()
        create_extended_warranty_jv(self)
