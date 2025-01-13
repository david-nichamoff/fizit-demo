import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers import Web3Manager, ConfigManager
from api.interfaces import SettlementAPI, ContractAPI, PartyAPI
from api.adapters.bank import MercuryAdapter, TokenAdapter

from api.mixins import ValidationMixin, AdapterMixin, InterfaceResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class ResidualAPI(ValidationMixin, AdapterMixin, InterfaceResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ResidualAPI, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize ResidualAPI with necessary dependencies."""
        if not hasattr(self, "initialized"):
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.w3_manager = Web3Manager()
            self.w3_contract = self.w3_manager.get_web3_contract()
            self.settlement_api = SettlementAPI()
            self.contract_api = ContractAPI()
            self.party_api = PartyAPI()

            self.mercury_adapter = MercuryAdapter()
            self.token_adapter = TokenAdapter()

            self.wallet_addr = self.config_manager.get_nested_config_value("wallet_addr", "Transactor")
            self.logger = logging.getLogger(__name__)
            self.initialized = True

    def get_residuals(self, contract_idx):
        """Retrieve residuals for a given contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            residuals = []

            response = self.settlement_api.get_settlements(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                settlements = response["data"]
                log_info(self.logger, f"Checking settlements for residuals: {settlements}")

            response = self.party_api.get_parties(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
                log_info(self.logger, f"Checking parties for residuals: {parties}")

            response = self.contract_api.get_contract(contract_idx)
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Contract for residuals: {contract}")

            seller_addr, funder_addr = self._get_party_addresses(parties)

            for settle in settlements:
                if Decimal(settle["residual_calc_amt"]) > Decimal(0.00) and settle["residual_pay_amt"] == "0.00":
                    residual = self._build_residual_dict(contract, settle, seller_addr, funder_addr)
                    residuals.append(residual)

            success_message = f"Retrieved {len(residuals)} residuals for contract {contract_idx}"
            return self._format_success(residuals, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation erorr retrieving residuals for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving residuals for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_residuals(self, contract_idx, residuals):
        """Add residual payments for a contract."""
        try:
            self._validate_contract_idx(contract_idx, self.contract_api)

            processed_count = 0
            for residual in residuals:
                self._process_residual_payment(residual, contract_idx)
                self._post_residual_on_blockchain(residual, contract_idx)
                processed_count += 1

            success_message = f"Successfully added {processed_count} residuals for contract {contract_idx}"
            return self._format_success({"count" : processed_count}, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Validaton error processing residuals for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error processing residuals for contract {contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_party_addresses(self, parties):
        """Retrieve the addresses of the seller and funder."""
        try:
            seller_addr = next((party["party_addr"] for party in parties if party["party_type"] == "seller"), None)
            funder_addr = next((party["party_addr"] for party in parties if party["party_type"] == "funder"), None)
            return seller_addr, funder_addr

        except Exception as e:
            error_message = f"Error retrieving party addresses: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_residual_dict(self, contract, settle, recipient_addr, funder_addr):
        """Build a residual dictionary for a settlement."""
        try:
            residual_dict = {
                "contract_idx": contract["contract_idx"],
                "settle_idx": settle["settle_idx"],
                "bank": contract["funding_instr"]["bank"],
                "recipient_addr": recipient_addr,
                "funder_addr": funder_addr,
                "residual_calc_amt": settle["residual_calc_amt"],
            }

            optional_fields = ["account_id", "recipient_id", "token_symbol"]
            for field in optional_fields:
                if field in contract["funding_instr"]:
                    residual_dict[field] = contract["funding_instr"][field]

            return residual_dict

        except Exception as e:
            error_message = f"Error building residual dictionary: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _process_residual_payment(self, residual, contract_idx):
        """Process the residual payment through the appropriate bank adapter."""
        try:
            adapter = self._get_bank_adapter(residual["bank"])

            if residual["bank"] == "mercury":
                adapter.make_payment(
                    residual["account_id"], residual["recipient_id"], residual["residual_calc_amt"]
                )
            elif residual["bank"] == "token":
                adapter.make_payment(
                    residual["contract_idx"], residual["funder_addr"], residual["recipient_addr"],
                    residual["token_symbol"], residual["residual_calc_amt"]
                )

        except ValidationError as e:
            error_message = f"Validation error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error processing residual payment: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _post_residual_on_blockchain(self, residual, contract_idx):
        """Post the residual payment to the blockchain."""
        try:
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(Decimal(residual["residual_calc_amt"]) * 100)

            transaction = self.w3_contract.functions.payResidual(
                contract_idx, residual["settle_idx"], current_time, payment_amt
            ).build_transaction()

            tx_receipt = self.w3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_idx, "fizit")
            if tx_receipt["status"] != 1:
                raise RuntimeError

        except Exception as e:
            error_message = f"Blockchain transaction_failed"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e