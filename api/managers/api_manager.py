import logging

from api.interfaces import (
    PurchaseContractAPI, SaleContractAPI, AdvanceContractAPI,
    SaleSettlementAPI, AdvanceSettlementAPI,
    PurchaseTransactionAPI, SaleTransactionAPI, AdvanceTransactionAPI,
    SaleDepositAPI, AdvanceDepositAPI,
    PurchaseAdvanceAPI, AdvanceAdvanceAPI,
    AdvanceResidualAPI,
    SaleDistributionAPI,
    AccountAPI, RecipientAPI,
    PartyAPI, ArtifactAPI
)

from api.managers.app_context import AppContext
from api.utilities.logging import log_info, log_warning, log_error

class APIManager:

    def __init__(self, context: AppContext):
        self.context = context
        self.logger = logging.getLogger(__name__)

        # Save these for use in APIs that need them
        self.config_manager = context.config_manager
        self.domain_manager = context.domain_manager
        self.cache_manager = context.cache_manager

        # --- APIs ---

        self.contract_apis = {
            "purchase": PurchaseContractAPI(context),
            "sale": SaleContractAPI(context),
            "advance": AdvanceContractAPI(context),
        }

        self.settlement_apis = {
            "purchase": None,
            "sale": SaleSettlementAPI(context),
            "advance": AdvanceSettlementAPI(context),
        }

        self.transaction_apis = {
            "purchase": PurchaseTransactionAPI(context),
            "sale": SaleTransactionAPI(context),
            "advance": AdvanceTransactionAPI(context),
        }

        self.deposit_apis = {
            "purchase": None,
            "sale": SaleDepositAPI(context),
            "advance": AdvanceDepositAPI(context),
        }

        self.advance_apis = {
            "purchase": PurchaseAdvanceAPI(context),
            "sale": None,
            "advance": AdvanceAdvanceAPI(context),
        }

        self.distribution_apis = {
            "purchase": None,
            "sale": SaleDistributionAPI(context),
            "advance": None
        }

        self.residual_apis = {
            "purchase": None,
            "sale": None,
            "advance": AdvanceResidualAPI(context),
        }

        self.global_apis = {
            "account": AccountAPI(context),
            "party": PartyAPI(context),
            "recipient": RecipientAPI(context),
            "artifact": ArtifactAPI(context)
        }

    def get_contract_api(self, contract_type):
        return self.contract_apis.get(contract_type)

    def get_settlement_api(self, contract_type):
        return self.settlement_apis.get(contract_type)

    def get_transaction_api(self, contract_type):
        return self.transaction_apis.get(contract_type)

    def get_deposit_api(self, contract_type):
        return self.deposit_apis.get(contract_type)

    def get_advance_api(self, contract_type):
        return self.advance_apis.get(contract_type)

    def get_distribution_api(self, contract_type):
        return self.distribution_apis.get(contract_type)

    def get_residual_api(self, contract_type):
        return self.residual_apis.get(contract_type)

    def get_account_api(self):
        return self.global_apis.get("account")

    def get_recipient_api(self):
        return self.global_apis.get("recipient")

    def get_party_api(self):
        return self.global_apis.get("party")

    def get_artifact_api(self):
        return self.global_apis.get("artifact")