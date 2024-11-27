import logging
import datetime
from decimal import Decimal
from hexbytes import HexBytes
from eth_utils import to_checksum_address

from api.managers import Web3Manager, SecretsManager, ConfigManager
from api.interfaces import PartyAPI

from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

class TokenAdapter:
    _instance = None

    def __new__(cls, *args, **kwargs):
        """Ensure that only one instance of TokenAdapter is created (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super(TokenAdapter, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            """Initialize the TokenAdapter class with keys and config."""
            self.secrets_manager = SecretsManager()
            self.keys = self.secrets_manager.load_keys()
            self.config_manager = ConfigManager()
            self.config = self.config_manager.load_config()
            self.party_api = PartyAPI()

            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance(network="avalanche")

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Prevent reinitialization

            # Inject middleware for POA chains if necessary
            self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    def get_deposits(self, start_date, end_date, token_symbol, contract):
        """Retrieve deposits using Web3 for transfers on the Avalanche chain."""
        deposits = []

        try:
            # Retrieve parties
            parties = self.party_api.get_parties(contract["contract_idx"])
            buyer_addr = next(
                (party["party_addr"] for party in parties if party["party_type"] == "buyer"), None
            )
            funder_addr = next(
                (party["party_addr"] for party in parties if party["party_type"] == "funder"), None
            )
            if not buyer_addr or not funder_addr:
                raise ValueError("Buyer or Funder address not found for the contract.")

            # Convert addresses to checksum format
            buyer_addr = self.w3.to_checksum_address(buyer_addr)
            funder_addr = self.w3.to_checksum_address(funder_addr)

            # Get token contract details
            token_config = self.config_manager.get_config_value("token_addr")
            token_entry = next(
                (token for token in token_config if token["key"].lower() == token_symbol.lower()), None
            )
            if not token_entry:
                raise ValueError(f"Token configuration for {token_symbol} not found.")
            token_contract_addr = to_checksum_address(token_entry["value"])

            # Prepare topics for filtering
            transfer_event_signature = f"0x{self.w3.keccak(text='Transfer(address,address,uint256)').hex()}"
            buyer_topic = f"0x{buyer_addr.lower()[2:].zfill(64)}"
            funder_topic = f"0x{funder_addr.lower()[2:].zfill(64)}"

            # Determine block range
            from_block = self._get_block_from_date(start_date)
            to_block = self._get_block_from_date(end_date)

            # RPC block chunk limit
            max_blocks = 2048

            self.logger.info(f"Searching for deposits from block {from_block} to {to_block} in chunks of {max_blocks}.")

            # Fetch the token's decimals from the contract
            token_contract = self.w3.eth.contract(
                address=token_contract_addr, abi=self._get_erc20_abi()
            )
            decimals = token_contract.functions.decimals().call()

            # Break block range into chunks and query logs
            for start in range(from_block, to_block + 1, max_blocks):
                end = min(start + max_blocks - 1, to_block)
                self.logger.info(f"Querying blocks from {start} to {end}.")

                logs = self.w3.eth.get_logs({
                    "fromBlock": start,
                    "toBlock": end,
                    "address": token_contract_addr,
                    "topics": [transfer_event_signature, buyer_topic, funder_topic]
                })

                # Parse the logs into deposits
                for log in logs:
                    try:
                        self.logger.info(f"Processing log: {log}")

                        # Ensure the data field is a valid hexadecimal string
                        if isinstance(log["data"], HexBytes):
                            data_hex = log["data"].hex()  # Convert HexBytes to a proper hex string
                        elif isinstance(log["data"], str) and log["data"].startswith("0x"):
                            data_hex = log["data"]
                        else:
                            self.logger.error(f"Invalid log data format: {log['data']}")
                            continue

                        # Decode the transfer value
                        value = int(data_hex, 16)

                        # Adjust value to standard units using the token's decimals
                        deposit_amt = value / (10 ** decimals)

                        deposits.append({
                            "bank": "token",
                            "buyer_addr": buyer_addr,
                            "funder_addr": funder_addr,
                            "deposit_id": log["transactionHash"].hex(),
                            "deposit_amt": deposit_amt,
                            "deposit_dt": self._get_date_from_block(log["blockNumber"]),
                        })

                    except ValueError as e:
                        self.logger.error(f"Failed to parse log data: {log['data']} with error: {e}")
                    except Exception as e:
                        self.logger.error(f"Unexpected error processing log: {log} with error: {e}")

            return deposits

        except Exception as e:
            self.logger.error(f"Error retrieving deposits: {str(e)}")
            raise RuntimeError("Failed to retrieve deposits.") from e

    def _get_block_from_date(self, date):
        """Estimate the block number from a given date using Web3."""
        timestamp = int(date.timestamp())
        
        # Get the latest block to start the search range
        latest_block = self.w3.eth.get_block("latest")
        latest_block_number = latest_block.number
        latest_block_timestamp = latest_block.timestamp

        # If the date is after the latest block timestamp, use the latest block
        if timestamp >= latest_block_timestamp:
            return latest_block_number

        # Binary search for the block closest to the timestamp
        start_block = 0
        end_block = latest_block_number

        while start_block <= end_block:
            mid_block = (start_block + end_block) // 2
            mid_block_data = self.w3.eth.get_block(mid_block)

            if mid_block_data.timestamp < timestamp:
                start_block = mid_block + 1
            elif mid_block_data.timestamp > timestamp:
                end_block = mid_block - 1
            else:
                return mid_block

        # Return the closest block (end_block will be just before the timestamp)
        return end_block

    def _get_date_from_block(self, block_number):
        """Retrieve the date from a block number."""
        block = self.w3.eth.get_block(block_number)
        return datetime.datetime.fromtimestamp(block["timestamp"])

    def make_payment(self, contract_idx, funder_addr, recipient_addr, token_symbol, amount):
        """Initiate a token payment from the funder wallet to the recipient wallet."""
        try:
            funder_addr = to_checksum_address(funder_addr)
            recipient_addr = to_checksum_address(recipient_addr)

            self.logger.info(f"funder_addr: {funder_addr}")
            self.logger.info(f"recipient_addr: {recipient_addr}")

            # Retrieve token contract address from configuration
            token_config = self.config_manager.get_config_value("token_addr")
            if not token_config:
                error_message = "Token configurations are missing in the configuration."
                self.logger.error(error_message)
                return False, error_message

            self.logger.info(f"token_config: {token_config}")
            self.logger.info(f"token_symbol {token_symbol}")

            token_entry = next(
                (token for token in token_config if token["key"].lower() == token_symbol.lower()), None
            )
            if not token_entry:
                error_message = f"Token configuration for {token_symbol} not found."
                self.logger.error(error_message)
                return False, error_message

            self.logger.info(f"token_entry: {token_entry}")

            token_contract_addr = to_checksum_address(token_entry["value"])

            token_contract = self.w3.eth.contract(
                address=token_contract_addr, abi=self._get_erc20_abi()
            )

            self.logger.info(f"token_contract: {token_contract}")

            # Convert amount to the smallest unit of the token (e.g., wei for ERC-20)
            decimals = token_contract.functions.decimals().call()
            smallest_unit_amount = int(Decimal(amount) * (10 ** decimals))

            self.logger.info(f"decimals: {decimals}")
            self.logger.info(f"smallet_unit_amount: {smallest_unit_amount}")

            # Build the transaction
            nonce = self.w3.eth.get_transaction_count(funder_addr)
            transaction = token_contract.functions.transfer(
                recipient_addr, smallest_unit_amount
            ).build_transaction({
                'from': funder_addr,
                'nonce': nonce,
                'gas': self.config_manager.get_nested_config_value("gas", "limit", default=200000),
                'gasPrice': self.w3.eth.gas_price,
            })

            # Use Web3Manager to sign and send the transaction
            tx_receipt = self.w3_manager.send_signed_transaction(transaction, funder_addr, contract_idx, "avalanche")

            if tx_receipt["status"] == 1:
                self.logger.info(f"Token payment successful. TX hash: {tx_receipt['transactionHash'].hex()}")
                return True, None
            else:
                error_message = f"Token payment failed. TX hash: {tx_receipt['transactionHash'].hex()}"
                self.logger.error(error_message)
                return False, error_message

        except Exception as e:
            error_message = f"Unexpected error during token payment: {str(e)}"
            self.logger.error(error_message)
            return False, error_message

    def _get_erc20_abi(self):
        """Return the minimal ABI for ERC-20 tokens."""
        return [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]