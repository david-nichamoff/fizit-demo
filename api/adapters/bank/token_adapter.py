import logging
import datetime
from decimal import Decimal
from hexbytes import HexBytes
from eth_utils import to_checksum_address

from rest_framework.exceptions import ValidationError
from rest_framework import status

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import log_error, log_info, log_warning

class TokenAdapter(ResponseMixin):

    def __init__(self, context: AppContext):
        self.context = context
        self.config_manager = context.config_manager
        self.secrets_manager = context.secrets_manager
        self.domain_manager = context.domain_manager
        self.logger = logging.getLogger(__name__)

    # accounts and recipients are not applicable for wallets
    def get_accounts(self):
        return []
    def get_recipients(self):
        return []

    def get_deposits(self, start_date, end_date, network, token_symbol, parties):
        """Retrieve deposits using Web3 for transfers on the Avalanche chain."""
        try:
            parsed_parties = self._parse_parties(parties)
            token_contract, decimals = self._get_token_contract(network, token_symbol)

            buyer_addr = parsed_parties.get("buyer")
            funder_addr = parsed_parties.get("funder")
            counterparty = parsed_parties.get("counterparty")

            log_info(self.logger, f"Validating address for buyer {buyer_addr} and funder {funder_addr}")
            self._validate_addresses(buyer_addr, funder_addr)

            deposits = self._fetch_transfer_logs(
                network, buyer_addr, funder_addr, counterparty, token_contract, decimals, start_date, end_date
            )
            return deposits

        except Exception as e:
            error_message = f"Error retrieving deposits: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def make_payment(self, contract_type, contract_idx, funder_addr, recipient_addr, network, token_symbol, amount):
        """Initiate a token payment from the funder wallet to the recipient wallet."""
        token_contract, decimals = self._get_token_contract(network, token_symbol)
        checksum_funder_addr = self.context.web3_manager.get_checksum_address(funder_addr)
        checksum_recipient_addr = self.context.web3_manager.get_checksum_address(recipient_addr)

        try:
            # native payment
            if token_contract is None:
                transaction = self._make_native_payment(checksum_funder_addr, checksum_recipient_addr, network, amount)
            else:
                # erc token
                smallest_unit_amount = self._convert_to_smallest_unit(amount, decimals)
                transaction = self._make_token_payment(checksum_funder_addr, checksum_recipient_addr, token_contract, network, smallest_unit_amount)

            log_info(self.logger, f"Sending transaction: {transaction} from {checksum_funder_addr} for contract {contract_type}:{contract_idx} on {network}")
            tx_receipt = self.context.web3_manager.send_signed_transaction(
                transaction,  checksum_funder_addr, contract_type, contract_idx, network=network
            )
            log_info(self.logger, f"Received tx_receipt: {tx_receipt}")

            if tx_receipt == 'MfaRequired':
                log_info(self.logger,  f"Payment signed successfully. MFA approval required")
                return 'MfaRequired'
            elif tx_receipt["status"] == 1:
                tx_hash = tx_receipt["transactionHash"].hex()
                log_info(self.logger, f"Payment broadcast successful, tx_hash={tx_hash}")
                return tx_hash
            else:
                error_message = f"Payment failed, transaction receipt: {tx_receipt}" 
                log_error(self.logger, error_message)
                raise RuntimeError(error_message)

        except Exception as e:
            error_message = f"Unexpected error during token/native payment: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message) from e

    def _make_token_payment(self, checksum_funder_addr, checksum_recipient_addr, token_contract, network, smallest_unit_amount):
        log_info(self.logger, f"Sending {smallest_unit_amount} tokens from {checksum_funder_addr} to {checksum_recipient_addr}")

        try:
            transaction = token_contract.functions.transfer(
                checksum_recipient_addr, smallest_unit_amount
            ).build_transaction({'from': checksum_funder_addr})

            log_info(self.logger, f"Sending transaction {transaction}")

            return transaction

        except Exception as e:
            error_message = f"Unexpected error during token payment: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError from e

    def _make_native_payment(self, checksum_funder_addr, checksum_recipient_addr, network, amount):
        log_info(self.logger, f"Sending {amount} native token from {checksum_funder_addr} to {checksum_recipient_addr}")
        w3 = self.context.web3_manager.get_web3_instance(network)

        try:
            transaction = {
                "to": checksum_recipient_addr,
                "value": w3.to_wei(amount, 'ether')  # Always ether for native tokens
             }

            log_info(self.logger, f"Sending transaction {transaction}")
            
            return transaction

        except Exception as e:
            log_error(self.logger, "Native token transfer failed")
            raise RuntimeError from e

    # --- Helper Methods ---
    def _parse_parties(self, parties):
        """Retrieve buyer and funder addresses from the contract parties."""

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

    def _get_token_contract(self, network, token_symbol):
        """Retrieve the token contract instance and decimals."""
        w3 = self.context.web3_manager.get_web3_instance(network)

        if self.domain_manager.get_native_token_symbol(network) == token_symbol:
            return None, None

        token_addr = self.config_manager.get_token_address(network, token_symbol)
        token_checksum_addr = self.context.web3_manager.get_checksum_address(token_addr)

        if not token_checksum_addr:
            raise ValidationError(f"Token symbol {token_symbol} not found")

        token_contract = w3.eth.contract(address=token_checksum_addr, abi=self._get_erc20_abi())
        decimals = token_contract.functions.decimals().call()
        log_info(self.logger, f"Found token contract for {token_symbol} at {token_checksum_addr}, decimals={decimals}")

        return token_contract, decimals

    def _convert_to_smallest_unit(self, amount, decimals):
        """Convert amount to the smallest unit of the token."""
        try:
            return int(Decimal(amount) * (10 ** decimals))

        except Exception as e:
            error_message = f"Failed to convert amount {amount} to smallest unit: {e}"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message)

    def _fetch_transfer_logs(self, network, buyer_addr, funder_addr, counterparty, token_contract, decimals, start_date, end_date):
        """Fetch token transfer logs."""
        w3 = self.context.web3_manager.get_web3_instance(network)

        transfer_signature = w3.keccak(text="Transfer(address,address,uint256)").hex()
        if not transfer_signature.startswith("0x"):
            transfer_signature = f"0x{transfer_signature}"

        # Convert addresses to checksum format
        buyer_addr = to_checksum_address(buyer_addr)
        funder_addr = to_checksum_address(funder_addr)

        # Create 32-byte padded topics for buyer and funder
        buyer_topic = w3.to_hex(w3.to_bytes(hexstr=buyer_addr).rjust(32, b'\x00'))
        funder_topic = w3.to_hex(w3.to_bytes(hexstr=funder_addr).rjust(32, b'\x00'))

        log_info(self.logger, f"Transfer event signature: {transfer_signature}")
        log_info(self.logger, f"Buyer topic: {buyer_topic}")
        log_info(self.logger, f"Funder topic: {funder_topic}")
        log_info(self.logger, f"Token contract address: {token_contract.address}")

        try:
            from_block = self._get_block_from_date(network, start_date)
            to_block = self._get_block_from_date(network, end_date)
            max_blocks = 2048

            deposits = []
            for start in range(from_block, to_block + 1, max_blocks):
                end = min(start + max_blocks - 1, to_block)

                log_info(self.logger, f"Checking blocks {start} to {end}")

                logs = w3.eth.get_logs({
                    "fromBlock": start,
                    "toBlock": end,
                    "address": token_contract.address,
                    "topics": [transfer_signature, buyer_topic, funder_topic]
                })

                log_info(self.logger, f"logs: {logs}")

                deposits.extend(self._parse_logs(network, logs, decimals, counterparty))

            return deposits

        except Exception as e:
            error_message = f"Failed to fetch transfer logs"
            log_error(self.logger, error_message)
            raise RuntimeError(error_message)

    def _parse_logs(self, network, logs, decimals, counterparty):
        """Parse transfer logs into deposit records."""
        deposits = []

        for log in logs:
            try:
                value = int(HexBytes(log["data"]).hex(), 16)
                deposit_amt = value / (10 ** decimals)
                deposits.append({
                    "bank": "token",
                    "tx_hash": f"0x{log["transactionHash"].hex()}",
                    "deposit_amt": deposit_amt,
                    "deposit_dt": self._get_date_from_block(network, log["blockNumber"]),
                    'counterparty' : counterparty
                })
            except Exception as e:
                error_message = f"Failed to parse transfer logs"
                log_error(self.logger, error_message)
                raise RuntimeError(error_message)

        return deposits

    def _get_block_from_date(self, network, date):
        """Estimate the block number from a given date using Web3."""
        log_info(self.logger, f"Retrieving blocks from date {date} for network {network}")
        timestamp = int(date.timestamp())

        w3 = self.context.web3_manager.get_web3_instance(network)
        if not w3:
            log_error(self.logger, f"Web3 instance for network '{network}' is None!")
            raise RuntimeError(f"Web3 not initialized for network '{network}'")

        log_info(self.logger, f"Connected to Web3: {w3.client_version}")

        try:
            latest_block = w3.eth.get_block("latest")
            if timestamp >= latest_block.timestamp:
                return latest_block.number

            start_block, end_block = 0, latest_block.number
            while start_block <= end_block:
                mid_block = (start_block + end_block) // 2
                log_info(self.logger, f"Binary search: start={start_block}, mid={mid_block}, end={end_block}")

                try:
                    mid_block_data = w3.eth.get_block(mid_block)
                except Exception as block_error:
                    log_error(self.logger, f"Error retrieving block {mid_block}: {block_error}")
                    raise

                mid_block_data = w3.eth.get_block(mid_block)
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

    def _get_date_from_block(self, network, block_number):
        """Retrieve the date from a block number."""
        w3 = self.context.web3_manager.get_web3_instance(network)

        try:
            block = w3.eth.get_block(block_number)
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

    def _get_web3(self, network):
        return self.context.web3_manager.get_web3_instance(network)