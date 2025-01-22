import logging
import os
import json
import requests
import urllib.parse

from datetime import datetime

from eth_utils import keccak, to_checksum_address
from web3 import Web3, HTTPProvider
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

from api.managers import SecretsManager, ConfigManager
from api.models.event_model import Event

from api.utilities.logging import log_error, log_info, log_warning

class Web3Manager():

    _instance = None
    _web3_instances = {}
    _abi = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(Web3Manager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.secrets_manager = SecretsManager()
            self.config_manager = ConfigManager()
            self.keys = self.secrets_manager.load_keys()
            self.config = self.config_manager.load_config()
            self.logger = logging.getLogger(__name__)

    def get_web3_instance(self, network="fizit"):
        """Get or create the Web3 instance for the specified network."""
        if network not in self._web3_instances:
            try:
                rpc_url = self._get_rpc_url(network)
                web3_instance = self._initialize_web3_instance(rpc_url, network)
                self._web3_instances[network] = web3_instance
            except Exception as e:
                log_error(self.logger, f"Failed to initialize Web3 instance for {network}: {e}")
                raise
        return self._web3_instances[network]

    def _get_rpc_url(self, network):
        """Retrieve the RPC URL for the specified network from the configuration."""
        rpc_config = self.config_manager.get_config_value("rpc")
        if not isinstance(rpc_config, list):
            raise ValueError("'rpc' configuration is not a list.")
        rpc_entry = next((rpc for rpc in rpc_config if rpc.get("key") == network), None)
        if not rpc_entry:
            raise ValueError(f"RPC URL for network '{network}' not found in configuration.")
        return rpc_entry.get("value")

    def _initialize_web3_instance(self, rpc_url, network):
        """Initialize and configure a Web3 instance."""
        web3_instance = Web3(HTTPProvider(rpc_url))
        if not web3_instance.is_connected():
            raise ConnectionError(f"Failed to connect to the RPC for network '{network}'")
        if network == "fizit":
            web3_instance.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        log_info(self.logger, f"Web3 connection established for {network}")
        return web3_instance

    def get_web3_contract(self, network="fizit"):
        """Get the Web3 contract instance for the specified network."""
        web3_instance = self.get_web3_instance(network)
        contract_address = self.config.get("contract_addr")
        if not contract_address:
            raise ValueError("Contract address is missing in configuration")
        return web3_instance.eth.contract(abi=self.load_abi(), address=contract_address)

    def get_nonce(self, wallet_addr, network="fizit"):
        """Get the transaction nonce for a wallet."""
        web3_instance = self.get_web3_instance(network)
        return web3_instance.eth.get_transaction_count(to_checksum_address(wallet_addr))

    def get_checksum_address(self, wallet_addr):
        """Convert an address to checksum format."""
        return to_checksum_address(wallet_addr)

    def load_abi(self):
        """Load the contract ABI from file."""
        if self._abi is None:
            abi_file_path = os.path.join(os.path.dirname(__file__), '../contract/delivery_abi.json')
            if not os.path.exists(abi_file_path):
                raise FileNotFoundError(f"ABI file not found: {abi_file_path}")
            try:
                with open(abi_file_path) as abi_file:
                    self._abi = json.load(abi_file)
            except json.JSONDecodeError as e:
                log_error(self.logger, f"Failed to parse ABI JSON: {e}")
                raise
            except Exception as e:
                log_error(self.logger, f"Error loading ABI: {e}")
                raise
        return self._abi

    def send_signed_transaction(self, transaction, wallet_addr, contract_idx, network="fizit"):
        """Send a signed transaction using the signing API."""
        web3_instance = self.get_web3_instance(network)
        wallet_addr = to_checksum_address(wallet_addr)

        log_info(self.logger, f"web3_instance: {network}, wallet_addr: {wallet_addr}")

        # Ensure 'from' is set to wallet_addr if not provided
        if "from" not in transaction or not transaction["from"]:
            transaction["from"] = wallet_addr
            log_info(self.logger, f"'from' address set to: {wallet_addr}")

        log_info(self.logger, f"transaction: {transaction}")

        if not web3_instance.is_connected():
            log_error(self.logger, "Web3 instance is not connected")
            raise ConnectionError("Web3 instance is not connected")

        try:
            chain_id = self._get_chain_id(network)
            log_info(self.logger, f"chain_id: {chain_id}")

            gas_limit, max_fee_per_gas, max_priority_fee_per_gas = self._estimate_gas_fees(web3_instance, transaction)
            log_info(self.logger, f"gas_limit: {gas_limit}, max_fee_per_gas: {max_fee_per_gas}, max_priority_fee_per_gas: {max_priority_fee_per_gas}")

            nonce = self.get_nonce(wallet_addr, network)
            log_info(self.logger, f"nonce: {nonce}")

            tx_data = {
                "chain_id": chain_id,
                "tx": {
                    "chain_id": hex(chain_id),
                    "gas": hex(gas_limit),
                    "maxFeePerGas": hex(max_fee_per_gas),
                    "maxPriorityFeePerGas": hex(max_priority_fee_per_gas),
                    "nonce": hex(nonce),
                    "to": transaction["to"],
                    "type": "0x2",
                    "value": hex(transaction["value"]),
                    "data": transaction.get("data", "0x"),
                },
            }

            log_info(self.logger, f"Sending tx_data: {tx_data}")

            signed_tx = self._sign_transaction(tx_data, wallet_addr)
            return self._broadcast_transaction(web3_instance, signed_tx, wallet_addr, transaction, contract_idx, network)

        except Exception as e:
            log_error(self.logger, f"Error sending signed transaction: {e}")
            raise

    def _get_chain_id(self, network):
        """Retrieve the chain ID for the specified network."""
        chain_config = self.config_manager.get_config_value("chain")
        chain_entry = next((item for item in chain_config if item["key"] == network), None)
        if not chain_entry:
            raise ValueError(f"Chain ID for network '{network}' not found in configuration.")
        return chain_entry["value"]

    def _estimate_gas_fees(self, web3_instance, transaction):

        log_info(self.logger, f"transaction details for estimating gas: {transaction}")

        """Estimate gas fees for a transaction."""
        estimated_gas = web3_instance.eth.estimate_gas({
            "from": transaction["from"],
            "to": transaction["to"],
            "from": transaction["from"],
            "data": transaction.get("data", "0x"),
            "value": transaction["value"],
        })

        log_info(self.logger, f"estimated gas: {estimated_gas}")

        block_gas_limit = web3_instance.eth.get_block("latest")["gasLimit"]
        gas_limit = min(estimated_gas, block_gas_limit)
        pool_min_fee_cap = web3_instance.to_wei('25', 'gwei')
        max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')
        max_fee_per_gas = pool_min_fee_cap + web3_instance.to_wei('10', 'gwei')

        return gas_limit, max_fee_per_gas, max_priority_fee_per_gas

    def _sign_transaction(self, tx_data, wallet_addr):
        """Sign a transaction using the signing API."""
        cs_url = self.config_manager.get_nested_config_value("cs", "url")
        org_id = urllib.parse.quote(self.config_manager.get_nested_config_value("cs", "org_id"), safe="")
        api_url = f"{cs_url}/v1/org/{org_id}/eth1/sign/{wallet_addr}"
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "Authorization": self.keys.get("role_session_token"),
        }
        response = requests.post(api_url, json=tx_data, headers=headers)
        response.raise_for_status()
        signed_tx = response.json().get("rlp_signed_tx")
        if not signed_tx:
            raise ValueError("Signed transaction not found in response")
        return signed_tx

    def _broadcast_transaction(self, web3_instance, signed_tx, wallet_addr, transaction, contract_idx, network):
        """Broadcast the signed transaction to the network."""
        tx_hash = web3_instance.eth.send_raw_transaction(web3_instance.to_bytes(hexstr=signed_tx))
        tx_receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        Event.objects.create(
            contract_idx=contract_idx,
            network=network,
            from_addr=wallet_addr,
            to_addr=transaction["to"],
            tx_hash=tx_hash.hex(),
            event_type="TransactionSent",
            details="Pending",
            status="pending",
        )
        return tx_receipt


    def send_contract_deployment(self, bytecode, abi, wallet_addr, network="fizit"):
        web3_instance = self.get_web3_instance(network)
        wallet_addr = to_checksum_address(wallet_addr)

        if not web3_instance.is_connected():
            logging.error(f"Web3 instance is not connected to the {network} network.")
            raise ConnectionError("Web3 instance is not connected")

        org_id = self.config_manager.get_nested_config_value("cs", "org_id")
        encoded_org_id = urllib.parse.quote(org_id, safe='')

        role_session_token = self.keys.get("role_session_token")
        if not role_session_token:
            raise ValueError("Session token is missing in the configuration")

        chain_config = self.config_manager.get_config_value("chain")
        chain_entry = next((item for item in chain_config if item["key"] == network), None)
        if not chain_entry:
            raise ValueError(f"Chain ID for network '{network}' not found in configuration.")
        
        chain_id = chain_entry["value"]
        
        try:
            # Prepare the contract data
            nonce = web3_instance.eth.get_transaction_count(wallet_addr)
            
            # Set a manually high gas limit
            gas_limit = 9_000_000  # Reasonably high limit for large contracts
            
            # Use fixed gas fees for simplicity
            max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')  # Priority fee
            max_fee_per_gas = web3_instance.to_wei('100', 'gwei')  # Max fee per gas

            log_info(self.logger, f"Deployment Details")
            log_info(self.logger, f"Wallet Address: {wallet_addr}")
            log_info(self.logger, f"Gas Limit: {gas_limit}")
            log_info(self.logger, f"maxFeePerGas: {max_fee_per_gas}")
            log_info(self.logger, f"maxPriorityFeePerGas: {max_priority_fee_per_gas}")
                
            # Build transaction
            tx = {
                "from": wallet_addr,
                "nonce": nonce,
                "value": 0,  # Contract deployments typically have no ETH value
                "to": None,  # Contract deployment transaction
                "gas": gas_limit,
                "maxFeePerGas": max_fee_per_gas,
                "maxPriorityFeePerGas": max_priority_fee_per_gas,
                "type": "0x2",  # EIP-1559 transaction type
                "data": bytecode
            }

            # Signing API payload
            tx_data = {
                "chain_id": chain_id,
                "tx": {key: (hex(value) if isinstance(value, int) else value) for key, value in tx.items()}
            }

            cs_url = self.config_manager.get_nested_config_value("cs", "url")
            api_url = f"{cs_url}/v1/org/{encoded_org_id}/eth1/sign/{wallet_addr}"
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": f"{role_session_token}"
            }

            # Send signing request
            response = requests.post(api_url, json=tx_data, headers=headers)
            response.raise_for_status()

            signed_tx = response.json().get("rlp_signed_tx")
            if not signed_tx:
                raise ValueError("Signed transaction not found in response")

            signed_tx_bytes = web3_instance.to_bytes(hexstr=signed_tx)

            # Send the transaction to the network
            tx_hash = web3_instance.eth.send_raw_transaction(signed_tx_bytes)

            # Wait for transaction receipt
            tx_receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            return tx_receipt

        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending request to signing API: {str(e)}")
            raise

        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            raise
