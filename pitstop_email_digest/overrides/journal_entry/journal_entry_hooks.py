from automotive.overrides.journal_entry.journal_entry_hooks import JournalEntryAuto

from ...utils.extended_warranty.validate_extended_warranty_voucher import (
    validate_extended_warranty_voucher,
)


class JournalEntryPitstopEmailDigest(JournalEntryAuto):
    def validate(self):
        super().validate()
        validate_extended_warranty_voucher(self)
