import logging
import datetime
from decimal import Decimal
from hexbytes import HexBytes

from eth_utils import to_checksum_address

from api.managers import Web3Manager, SecretsManager, ConfigManager
from api.interfaces import PartyAPI

from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from web3 import Web3

from rest_framework.exceptions import ValidationError
from rest_framework import status

from api.mixins.interfaces import InterfaceResponseMixin
from api.utilities.logging import log_error, log_info, log_warning

class TokenAdapter(InterfaceResponseMixin):
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that only one instance of TokenAdapter is created (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(TokenAdapter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.secrets_manager = SecretsManager()
            self.keys = self.secrets_manager.load_keys()
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.party_api = PartyAPI()
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance(network="avalanche")
            self.logger = logging.getLogger(__name__)

            self.initialized = True

            # Inject middleware for POA chains if necessary
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    def get_deposits(self, start_date, end_date, token_symbol, contract):
        """Retrieve deposits using Web3 for transfers on the Avalanche chain."""
        try:
            parties = self._get_parties(contract["contract_idx"])
            token_contract, decimals = self._get_token_contract(token_symbol)

            buyer_addr = parties.get("buyer")
            funder_addr = parties.get("funder")
            counterparty = parties.get("counterparty")

            log_info(self.logger, f"Validating address for buyer {buyer_addr} and funder {funder_addr}")
            self._validate_addresses(buyer_addr, funder_addr)

            deposits = self._fetch_transfer_logs(
                buyer_addr, funder_addr, counterparty, token_contract, decimals, start_date, end_date
            )
            return deposits

        except Exception as e:
            error_message = f"Error retrieving deposits: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def make_payment(self, contract_idx, funder_addr, recipient_addr, token_symbol, amount):
        """Initiate a token payment from the funder wallet to the recipient wallet."""

        try:
            token_contract, decimals = self._get_token_contract(token_symbol)
            smallest_unit_amount = self._convert_to_smallest_unit(amount, decimals)

            checksum_funder_addr = self.w3_manager.get_checksum_address(funder_addr)
            checksum_recipient_addr = self.w3_manager.get_checksum_address(recipient_addr)

            log_info(self.logger, f"Sending {smallest_unit_amount} tokens from {checksum_funder_addr} to {checksum_recipient_addr}")

            transaction = token_contract.functions.transfer(
                checksum_recipient_addr, smallest_unit_amount
            ).build_transaction({'from': checksum_funder_addr})

            log_info(self.logger, f"Sending transaction {transaction}")

            tx_receipt = self.w3_manager.send_signed_transaction(
                transaction, funder_addr, contract_idx, network="avalanche"
            )

            if tx_receipt["status"] == 1:
                log_info(self.logger,  f"Token payment successful. TX hash: {tx_receipt['transactionHash'].hex()}")
            else:
                error_message = f"Token payment failed. TX hash: {tx_receipt['transactionHash'].hex()}"
                log_error(self.logger, error_message)
                raise RuntimeError

        except Exception as e:
            error_message = f"Unexpected error during token payment: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError from e

    # --- Helper Methods ---
    def _get_parties(self, contract_idx):
        """Retrieve buyer and funder addresses from the contract parties."""
        response = self.party_api.get_parties(contract_idx)
        if response["status"] == status.HTTP_200_OK:
            parties = response["data"]

        buyer_addr = next((party["party_addr"] for party in parties if party["party_type"] == "buyer"), None)
        funder_addr = next((party["party_addr"] for party in parties if party["party_type"] == "funder"), None)
        counterparty = next((party["party_code"] for party in parties if party["party_type"] == "buyer"), None)

        return {"buyer": buyer_addr, "funder": funder_addr, "counterparty": counterparty}

    def _validate_addresses(self, buyer_addr, funder_addr):
        """Validate buyer and funder addresses."""
        if not buyer_addr or not funder_addr:
            error_message = "Buyer or Funder address not found for the contract."
            log_error(self.logger, error_message)
            raise ValidationError(error_message)

    def _get_token_contract(self, token_symbol):
        """Retrieve the token contract instance and decimals."""
        token_config = self.config_manager.get_config_value("token_addr")
        token_entry = next((token for token in token_config if token["key"].lower() == token_symbol.lower()), None)

        try:
            if not token_entry:
                raise ValidationError(f"Token symbol {token_symbol} not found")

            token_contract_addr = self.w3_manager.get_checksum_address(token_entry["value"])
            log_info(self.logger, f"Found token contract address for {token_symbol}: {token_contract_addr}")

            token_contract = self.w3.eth.contract(address=token_contract_addr, abi=self._get_erc20_abi())
            decimals = token_contract.functions.decimals().call()
            log_info(self.logger, f"Found decimals for {token_symbol}: {decimals}")


            return token_contract, decimals

        except ValidationError as e:
            error_message = f"Validation error getting token contract: {e}"
            log_error(self.logger, error_message)
            raise ValidationError(error_message) from e
        except Exception as e:
            error_message = f"Unexpected error getting token contract: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _convert_to_smallest_unit(self, amount, decimals):
        """Convert amount to the smallest unit of the token."""
        try:
            return int(Decimal(amount) * (10 ** decimals))

        except Exception as e:
            error_message = f"Failed to convert amount {amount} to smallest unit: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message)

    def _fetch_transfer_logs(self, buyer_addr, funder_addr, counterparty, token_contract, decimals, start_date, end_date):
        """Fetch token transfer logs."""
        transfer_signature = self.w3.keccak(text="Transfer(address,address,uint256)").hex()
        if not transfer_signature.startswith("0x"):
            transfer_signature = f"0x{transfer_signature}"

        # Convert addresses to checksum format
        buyer_addr = to_checksum_address(buyer_addr)
        funder_addr = to_checksum_address(funder_addr)

        # Create 32-byte padded topics for buyer and funder
        buyer_topic = self.w3.to_hex(self.w3.to_bytes(hexstr=buyer_addr).rjust(32, b'\x00'))
        funder_topic = self.w3.to_hex(self.w3.to_bytes(hexstr=funder_addr).rjust(32, b'\x00'))

        log_info(self.logger, f"Transfer event signature: {transfer_signature}")
        log_info(self.logger, f"Buyer topic: {buyer_topic}")
        log_info(self.logger, f"Funder topic: {funder_topic}")
        log_info(self.logger, f"Token contract address: {token_contract.address}")

        try:
            from_block = self._get_block_from_date(start_date)
            to_block = self._get_block_from_date(end_date)
            max_blocks = 2048

            deposits = []
            for start in range(from_block, to_block + 1, max_blocks):
                end = min(start + max_blocks - 1, to_block)

                log_info(self.logger, f"Checking blocks {start} to {end}")

                logs = self.w3.eth.get_logs({
                    "fromBlock": start,
                    "toBlock": end,
                    "address": token_contract.address,
                    "topics": [transfer_signature, buyer_topic, funder_topic]
                })

                log_info(self.logger, f"logs: {logs}")

                deposits.extend(self._parse_logs(logs, decimals, counterparty))

            return deposits

        except Exception as e:
            error_message = f"Failed to fetch transfer logs"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message)

    def _parse_logs(self, logs, decimals, counterparty):
        """Parse transfer logs into deposit records."""
        deposits = []

        for log in logs:
            try:
                value = int(HexBytes(log["data"]).hex(), 16)
                deposit_amt = value / (10 ** decimals)
                deposits.append({
                    "bank": "token",
                    "deposit_id": log["transactionHash"].hex(),
                    "deposit_amt": deposit_amt,
                    "deposit_dt": self._get_date_from_block(log["blockNumber"]),
                    'counterparty' : counterparty
                })
            except Exception as e:
                error_message = f"Failed to parse transfer logs"
                log_error(self.logger, error_message)
                raise RuntimeError(error_message)

        return deposits

    def _get_block_from_date(self, date):
        """Estimate the block number from a given date using Web3."""
        timestamp = int(date.timestamp())

        try:
            latest_block = self.w3.eth.get_block("latest")
            if timestamp >= latest_block.timestamp:
                return latest_block.number

            start_block, end_block = 0, latest_block.number
            while start_block <= end_block:
                mid_block = (start_block + end_block) // 2
                mid_block_data = self.w3.eth.get_block(mid_block)
                if mid_block_data.timestamp < timestamp:
                    start_block = mid_block + 1
                elif mid_block_data.timestamp > timestamp:
                    end_block = mid_block - 1
                else:
                    return mid_block

            return end_block

        except Exception as e:
            error_message = f"Failed to retrieve blocks from date"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message)

    def _get_date_from_block(self, block_number):
        """Retrieve the date from a block number."""
        try:
            block = self.w3.eth.get_block(block_number)
            return datetime.datetime.fromtimestamp(block["timestamp"])

        except Exception as e:
            error_message = f"Failed to get date from block"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message)

    def _get_erc20_abi(self):
        """Return the minimal ABI for ERC-20 tokens."""
        return [
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"},
        ]