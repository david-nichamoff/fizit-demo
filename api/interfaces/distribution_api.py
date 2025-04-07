import datetime
import logging
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import  log_error, log_info, log_warning

class BaseDistributionAPI(ResponseMixin):
    def __init__(self, context: AppContext):
        self.context = context
        self.config_manager = context.config_manager
        self.domain_manager = context.domain_manager
        self.cache_manager = context.cache_manager
        self.wallet_addr = self.config_manager.get_wallet_address("Transactor")
        self.logger = logging.getLogger(__name__)

    def get_distributions(self, contract, parties, settlements):
        """Retrieve distributions for a given contract."""
        try:
            settlement_api = self.context.api_manager.get_settlement_api(contract["contract_type"])
            response = settlement_api.get_settlements(contract["contract_type"], contract["contract_idx"])
            if response["status"] == status.HTTP_200_OK:
                settlements = response["data"]
                log_info(self.logger, f"Checking settlements for distributions: {settlements}")

            party_api = self.context.api_manager.get_party_api()
            response = party_api.get_parties(contract["contract_type"], contract["contract_idx"])
            if response["status"] == status.HTTP_200_OK:
                parties = response["data"]
                log_info(self.logger, f"Checking parties for distributions: {parties}")

            contract_api = self.context.api_manager.get_contract_api(contract["contract_type"])
            response = contract_api.get_contract(contract["contract_type"], contract["contract_idx"])
            if response["status"] == status.HTTP_200_OK:
                contract = response["data"]
                log_info(self.logger, f"Contract for distributions: {contract}")

            client_addr, funder_addr = self._get_party_addresses(parties)

            distributions = []
            for settle in settlements:
                if Decimal(settle["dist_calc_amt"]) > Decimal(0.00) and settle["dist_pay_amt"] == "0.00":
                    distribution = self._build_distribution_dict(contract["contract_type"], contract, settle, client_addr, funder_addr)
                    distributions.append(distribution)

            success_message = f"Retrieved {len(distributions)} distributions for {contract["contract_type"]}:{contract["contract_idx"]}"
            return self._format_success(distributions, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error retrieving distributions for {contract["contract_type"]}:{contract["contract_idx"]}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving distributions for {contract["contract_type"]}:{contract["contract_idx"]}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_distributions(self, contract_type, contract_idx, distributions):
        """Add distribution payments for a contract."""
        try:
            self.cache_manager.delete(self.cache_manager.get_transaction_cache_key(contract_type, contract_idx))
            self.cache_manager.delete(self.cache_manager.get_settlement_cache_key(contract_type, contract_idx))

            processed_count = 0
            for distribution in distributions:
                tx_hash = self._process_distribution_payment(distribution, contract_type, contract_idx)
                self._post_distribution_on_blockchain(distribution, contract_type, contract_idx, tx_hash)
                processed_count += 1

            success_message = f"Successfully added {processed_count} distributions for {contract_type}:{contract_idx}"
            return self._format_success({"count" : processed_count}, success_message, status.HTTP_201_CREATED)

        except ValidationError as e:
            error_message = f"Validaton error processing distributions for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error processing distributions for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_party_addresses(self, parties):
        """Retrieve the addresses of the seller and funder."""
        try:
            client_addr = next((party["party_addr"] for party in parties if party["party_type"] == "client"), None)
            funder_addr = next((party["party_addr"] for party in parties if party["party_type"] == "funder"), None)
            return client_addr, funder_addr

        except Exception as e:
            error_message = f"Error retrieving party addresses: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_distribution_dict(self, contract_type, contract, settle, recipient_addr, funder_addr):
        """Build a distribution dictionary for a settlement."""
        try:
            distribution_dict = {
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "contract_name" : contract["contract_name"],
                "settle_idx": settle["settle_idx"],
                "settle_due_dt": settle["settle_due_dt"],
                "bank": contract["funding_instr"]["bank"],
                "recipient_addr": recipient_addr,
                "funder_addr": funder_addr,
                "distribution_calc_amt": settle["dist_calc_amt"],
            }

            optional_fields = ["account_id", "recipient_id", "token_symbol", "network"]
            for field in optional_fields:
                if field in contract["funding_instr"]:
                    distribution_dict[field] = contract["funding_instr"][field]

            return distribution_dict

        except Exception as e:
            error_message = f"Error building distribution dictionary: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _process_distribution_payment(self, distribution, contract_type, contract_idx):
        """Process the distribution payment through the appropriate bank adapter."""
        try:
            adapter = self.context.adapter_manager.get_bank_adapter(distribution["bank"])
            required_fields = self.domain_manager.get_bank_payment_fields(distribution["bank"])

            mapped_distribution = self.domain_manager.map_payment_fields(distribution)
            payment_params = {field: mapped_distribution[field] for field in required_fields}
            tx_hash = adapter.make_payment(**payment_params)

            return tx_hash

        except ValidationError as e:
            error_message = f"Validation error processing payment: {str(e)}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Error processing distribution payment: {str(e)}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _post_distribution_on_blockchain(self, distribution, contract_type, contract_idx, tx_hash):
        """Post the distribution payment to the blockchain."""
        try:
            current_time = int(datetime.datetime.now().timestamp())
            payment_amt = int(Decimal(distribution["distribution_calc_amt"]) * 100)

            log_info(self.logger, f"contract_idx:{contract_idx},settle_idx: {distribution["settle_idx"]}")
            log_info(self.logger, f"current_time:{current_time},payment_amt: {payment_amt}, tx_hash:{tx_hash}")

            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            transaction = web3_contract.functions.payDistribution(
                contract_idx, distribution["settle_idx"], current_time, payment_amt, tx_hash
            ).build_transaction()

            network = self.domain_manager.get_contract_network()
            tx_receipt = self.context.web3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, network)

            if tx_receipt["status"] != 1:
                raise RuntimeError

        except Exception as e:
            error_message = f"Blockchain transaction_failed"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### **Subclass for Advance Contracts**
class SaleDistributionAPI(BaseDistributionAPI):
    pass
