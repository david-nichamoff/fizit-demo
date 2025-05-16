import logging

from frontend.forms.admin import (
    PurchaseContractForm, AdvanceContractForm, SaleContractForm,
    SaleSettlementForm, AdvanceSettlementForm
)

from api.utilities.logging import log_info, log_warning, log_error

class FormManager:

    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)

        self.contract_forms = {
            "purchase": PurchaseContractForm,
            "advance": AdvanceContractForm,
            "sale": SaleContractForm
        }

        self.settlement_forms = {
            "advance": AdvanceSettlementForm,
            "sale": SaleSettlementForm,
            "purchase": None
        }

    def get_contract_form(self, contract_type):
        return self.contract_forms.get(contract_type)

    def get_settlement_form(self, contract_type):
        return self.settlement_forms.get(contract_type)