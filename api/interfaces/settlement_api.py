import logging
import time
from decimal import Decimal

from rest_framework import status
from rest_framework.exceptions import ValidationError

from api.interfaces.mixins import ResponseMixin
from api.managers.app_context import AppContext
from api.interfaces.encryption_api import get_encryptor, get_decryptor
from api.utilities.formatting import from_timestamp, to_decimal
from api.utilities.logging import  log_error, log_info, log_warning

class BaseSettlementAPI(ResponseMixin):

    def __init__(self, context: AppContext): 
        self.context = context
        self.domain_manager = context.domain_manager
        self.config_manager = context.config_manager
        self.cache_manager = context.cache_manager
        self.wallet_addr = self.config_manager.get_wallet_address("transactor")
        self.logger = logging.getLogger(__name__)

    def get_settlements(self, contract_type, contract_idx, api_key=None, parties=[]):
        """Retrieve all settlements for a given contract while ensuring only encrypted values are cached."""
        try:
            cache_key = self.cache_manager.get_settlement_cache_key(contract_type, contract_idx)
            cached_settlements = self.cache_manager.get(cache_key)
            success_message = f"Successfully retrieved settlements for {contract_type}:{contract_idx}"

            contract_api = self.context.api_manager.get_contract_api(contract_type)
            contract = contract_api.get_contract(contract_type, contract_idx, api_key, parties).get("data")

            if cached_settlements is not None:
                log_info(self.logger, f"Loaded settlements for {contract_type}:{contract_idx} from cache")
                parsed_settlements = [
                    self._build_settlement_dict(settlement, idx, contract_type, contract, api_key, parties)
                    for idx, settlement in enumerate(cached_settlements)
                ]
                log_info(self.logger, f"Returning parsed settlements {parsed_settlements}")
                return self._format_success(parsed_settlements, success_message, status.HTTP_200_OK)

            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            raw_settlements = web3_contract.functions.getSettlements(contract["contract_idx"]).call()

            self.cache_manager.set(cache_key, raw_settlements, timeout=None)

            parsed_settlements = [
                self._build_settlement_dict(settlement, idx, contract_type, contract, api_key, parties)
                for idx, settlement in enumerate(raw_settlements)
            ]

            return self._format_success(parsed_settlements, success_message, status.HTTP_200_OK)

        except ValidationError as e:
            error_message = f"Validation error returning settlements for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error retrieving settlements for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def add_settlements(self, contract_type, contract_idx, settlements):
        """Add settlements to the blockchain for a given contract."""
        try:
            encryptor = get_encryptor()
            processed_count = 0

            for settlement in settlements:
                log_info(self.logger,f"Sending {settlement} to chain with {contract_type}:{contract_idx}")
                transaction = self._build_add_settlement(contract_type, contract_idx, settlement, encryptor)

                network = self.domain_manager.get_contract_network()
                tx_receipt = self.context.web3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, network)

                if tx_receipt["status"] != 1:
                    raise RuntimeError

                processed_count += 1

            # Sleep to give time for transaction to complete
            time.sleep(self.config_manager.get_network_sleep_time())

            cache_key = self.cache_manager.get_settlement_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

            success_message = f"Successfully added {processed_count} settlements for {contract_type}:{contract_idx}"
            return self._format_success({"count":processed_count}, success_message, status.HTTP_201_CREATED )

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error adding settlements for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete_settlements(self, contract_type, contract_idx):
        """Delete all settlements for a given contract."""
        try:
            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            transaction = web3_contract.functions.deleteSettlements(contract_idx).build_transaction()

            network = self.domain_manager.get_contract_network()
            tx_receipt = self.context.web3_manager.send_signed_transaction(transaction, self.wallet_addr, contract_type, contract_idx, network)

            if tx_receipt["status"] != 1:
                raise RuntimeError

            # Sleep to give time for transaction to complete
            time.sleep(self.config_manager.get_network_sleep_time())

            cache_key = self.cache_manager.get_settlement_cache_key(contract_type, contract_idx)
            self.cache_manager.delete(cache_key)

            success_message = f"All settlements deleted for {contract_type}:{contract_idx}"
            return self._format_success({"contract_idx" : contract_idx}, success_message, status.HTTP_204_NO_CONTENT)

        except ValidationError as e:
            error_message = f"Validation error for {contract_type}:{contract_idx}: {str(e)}"
            return self._format_error(error_message, status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            error_message = f"Error deleting settlements for {contract_type}:{contract_idx}: {e}"
            return self._format_error(error_message, status.HTTP_500_INTERNAL_SERVER_ERROR)


### **Subclass for Sale Contracts**
class SaleSettlementAPI(BaseSettlementAPI):
    def _build_settlement_dict(self, settle, idx, contract_type, contract, api_key, parties):
        """Build a settlement dictionary from raw data."""
        try:
            decryptor = get_decryptor(api_key, parties)
            decrypted_extended_data = decryptor.decrypt(settle[0])

            return {
                "extended_data": decrypted_extended_data,
                "settle_due_dt": from_timestamp(settle[1]),
                "settle_pay_dt": from_timestamp(settle[2]),
                "settle_exp_amt": to_decimal(settle[3]),
                "settle_pay_amt": to_decimal(settle[4]),
                "settle_tx_hash": settle[5],
                "days_late": settle[6],
                "late_fee_amt": to_decimal(settle[7]),
                "principal_amt": to_decimal(settle[8]),
                "dist_pay_dt": from_timestamp(settle[9]),
                "dist_pay_amt": to_decimal(settle[10]),
                "dist_calc_amt": to_decimal(settle[11]),
                "dist_tx_hash": settle[12],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "contract_name": contract["contract_name"],
                "funding_instr": contract["funding_instr"],
                "deposit_instr": contract["deposit_instr"],
                "settle_idx": idx
            }
        except Exception as e:
            error_message = f"Error building settlement dictionary for settlement {idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_add_settlement(self, contract_type, contract_idx, settlement, encryptor):
        """Build the transaction to add a settlement."""
        try:
            encrypted_data = encryptor.encrypt(settlement["extended_data"])
            due_dt = int(settlement["settle_due_dt"].timestamp())
            principal_amt = int(Decimal(settlement["principal_amt"]) * 100)
            settle_exp_amt = int(Decimal(settlement["settle_exp_amt"]) * 100) 

            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            return web3_contract.functions.addSettlement(
                contract_idx, encrypted_data, due_dt, principal_amt, settle_exp_amt
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building settlement transaction for {contract_type}:{contract_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

### **Subclass for Advance Contracts**
class AdvanceSettlementAPI(BaseSettlementAPI):
    def _build_settlement_dict(self, settle, idx, contract_type, contract, api_key, parties):
        """Build a settlement dictionary from raw data."""
        try:
            decryptor = get_decryptor(api_key, parties)
            decrypted_extended_data = decryptor.decrypt(settle[0])

            return {
                "extended_data": decrypted_extended_data,
                "settle_due_dt": from_timestamp(settle[1]),
                "transact_min_dt": from_timestamp(settle[2]),
                "transact_max_dt": from_timestamp(settle[3]),
                "transact_count": settle[4],
                "advance_amt": to_decimal(settle[5]),
                "advance_amt_gross": to_decimal(settle[6]),
                "settle_pay_dt": from_timestamp(settle[7]),
                "settle_exp_amt": to_decimal(settle[8]),
                "settle_pay_amt": to_decimal(settle[9]),
                "settle_tx_hash": settle[10],
                "dispute_amt": to_decimal(settle[11]),
                "dispute_reason": settle[12],
                "days_late": settle[13],
                "late_fee_amt": to_decimal(settle[14]),
                "residual_pay_dt": from_timestamp(settle[15]),
                "residual_pay_amt": to_decimal(settle[16]),
                "residual_exp_amt": to_decimal(settle[17]),
                "residual_calc_amt": to_decimal(settle[18]),
                "residual_tx_hash": settle[19],
                "contract_type": contract_type,
                "contract_idx": contract["contract_idx"],
                "contract_name": contract["contract_name"],
                "funding_instr": contract["funding_instr"],
                "deposit_instr": contract["deposit_instr"],
                "settle_idx": idx
            }
        except Exception as e:
            error_message = f"Error building settlement dictionary for settlement {idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _build_add_settlement(self, contract_type, contract_idx, settlement, encryptor):
        """Build the transaction to add a settlement."""
        try:
            encrypted_data = encryptor.encrypt(settlement["extended_data"])
            due_dt = int(settlement["settle_due_dt"].timestamp())
            min_dt = int(settlement["transact_min_dt"].timestamp())
            max_dt = int(settlement["transact_max_dt"].timestamp())

            network = self.domain_manager.get_contract_network()
            web3_contract = self.context.web3_manager.get_web3_contract(contract_type, network)
            return web3_contract.functions.addSettlement(
                contract_idx, encrypted_data, due_dt, min_dt, max_dt
            ).build_transaction()
        except Exception as e:
            error_message = f"Error building settlement transaction for {contract_type}:{contract_idx}: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

