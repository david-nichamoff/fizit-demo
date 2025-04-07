import logging

from api.adapters.bank import (
    MercuryAdapter, TokenAdapter, ManualAdapter
)

from api.utilities.logging import log_info, log_warning, log_error

class AdapterManager:

    def __init__(self, context):
        self.logger = logging.getLogger(__name__)

        self.bank_adapters = {
            "mercury": MercuryAdapter(context),
            "token": TokenAdapter(context),
            "manual": ManualAdapter(context)
        }   
        
    def get_bank_adapter(self, bank):
        return self.bank_adapters.get(bank)

