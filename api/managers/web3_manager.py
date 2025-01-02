import json
import logging
import os
import requests
import urllib.parse
import rlp

from hexbytes import HexBytes

from datetime import datetime

from web3 import Web3, HTTPProvider
from eth_utils import keccak, to_checksum_address, to_bytes
from eth_account._utils.legacy_transactions import Transaction
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

from api.managers import SecretsManager, ConfigManager
from api.models.event_model import Event 


class Web3Manager:
    _instance = None
    _web3_instances = {}  # Dictionary to hold Web3 instances for multiple networks
    _abi = None

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(Web3Manager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.secrets_manager = SecretsManager()
        self.config_manager = ConfigManager()

        self.keys = self.secrets_manager.load_keys()
        self.config = self.config_manager.load_config()

    def get_web3_instance(self, network="fizit"):
        """Get or create the Web3 instance for the specified network."""
        if network not in self._web3_instances:
            rpc_url = self._get_rpc_url(network)
            if not rpc_url:
                raise ValueError(f"RPC URL for network '{network}' is missing.")

            try:
                web3_instance = Web3(HTTPProvider(rpc_url))

                # Add the middleware to handle Proof of Authority chains if needed
                if network == "fizit":  # Assuming your private L1 uses PoA
                    web3_instance.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

                if web3_instance.is_connected():
                    print(f"Web3 connection successful for {network}")
                    self._web3_instances[network] = web3_instance
                else:
                    raise ConnectionError(f"Failed to connect to the RPC for network '{network}'")
            except Exception as e:
                print(f"Error connecting to the RPC for network '{network}': {e}")
                raise

        return self._web3_instances[network]

    def _get_rpc_url(self, network):
        """Retrieve the RPC URL for the specified network from the configuration."""
        try:
            # Ensure config is a dictionary
            if not isinstance(self.config, dict):
                raise ValueError("Configuration is not a dictionary.")

            # Get the "rpc" key
            rpc_config = self.config.get("rpc")
            if not isinstance(rpc_config, list):
                raise ValueError("'rpc' configuration is not a list.")

            # Find the RPC URL for the specified network
            rpc_entry = next((rpc for rpc in rpc_config if rpc.get("key") == network), None)
            if not rpc_entry:
                raise ValueError(f"RPC URL for network '{network}' not found in configuration.")

            return rpc_entry.get("value")
        except Exception as e:
            logging.exception("Error retrieving RPC URL.")
            raise


    def get_web3_contract(self, network="fizit"):
        """Get or create the Web3 contract instance for the specified network."""
        web3_instance = self.get_web3_instance(network)
        contract_address = self.config.get("contract_addr")

        if not contract_address:
            raise ValueError("Contract address is missing in configuration")

        return web3_instance.eth.contract(
            abi=self.load_abi(),
            address=contract_address
        )

    def get_nonce(self, wallet_addr, network="fizit"):
        web3_instance = self.get_web3_instance(network)
        return web3_instance.eth.get_transaction_count(wallet_addr)

    def get_checksum_address(self, wallet_addr):
        return to_checksum_address(wallet_addr)


    def load_abi(self):
        """Load the contract ABI from file."""
        if self._abi is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            abi_file_path = os.path.join(current_dir, '../contract/delivery_abi.json')

            if not os.path.exists(abi_file_path):
                raise FileNotFoundError(f"ABI file not found: {abi_file_path}")
            
            try:
                with open(abi_file_path) as abi_file:
                    self._abi = json.load(abi_file)

            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to decode ABI JSON: {e}")
            except Exception as e:
                raise RuntimeError(f"Error loading ABI: {e}")

        return self._abi

    def send_signed_transaction(self, transaction, wallet_addr, contract_idx, network="fizit"):
        web3_instance = self.get_web3_instance(network)
        wallet_addr = to_checksum_address(wallet_addr)

        # Check if web3 is connected before proceeding
        if not web3_instance.is_connected():
            logging.error(f"Web3 instance is not connected to the {network} network.")
            raise ConnectionError("Web3 instance is not connected")

        org_id = self.config_manager.get_nested_config_value("cs", "org_id")
        encoded_org_id = urllib.parse.quote(org_id, safe='')

        # Retrieve the session token from config or environment
        role_session_token = self.keys.get("role_session_token")
        if not role_session_token:
            raise ValueError("Session token is missing in the configuration")

        # Retrieve the chain ID for the specified network
        chain_config = self.config_manager.get_config_value("chain")
        chain_entry = next((item for item in chain_config if item["key"] == network), None)
        if not chain_entry:
            raise ValueError(f"Chain ID for network '{network}' not found in configuration.")

        chain_id = chain_entry["value"]

        try:
            # Estimate the gas required for the transaction
            estimated_gas = web3_instance.eth.estimate_gas({
                "from": wallet_addr,
                "to": transaction["to"],
                "data": transaction.get("data", "0x"),
                "value": transaction["value"],
            })
            block_gas_limit = web3_instance.eth.get_block("latest")["gasLimit"]

            # Set gas_limit to the smaller of the estimated gas and the block gas limit
            gas_limit = min(estimated_gas, block_gas_limit)

            # Adjust the gas fees
            pool_min_fee_cap = web3_instance.to_wei('25', 'gwei')  # Pool minimum fee cap
            max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')  # Slightly increase priority fee for faster inclusion
            max_fee_per_gas = max(pool_min_fee_cap, max_priority_fee_per_gas + web3_instance.to_wei('10', 'gwei'))

            logging.info(f"Estimated Gas: {estimated_gas}, Block Gas Limit: {block_gas_limit}")
            logging.info(f"Final Gas Limit: {gas_limit}")
            logging.info(f"Pool Min Fee Cap: {pool_min_fee_cap}")
            logging.info(f"Max priority fee per gas: {max_priority_fee_per_gas}")
            logging.info(f"Max fee per gas: {max_fee_per_gas}")

            # Estimate gas
            #block_gas_limit = web3_instance.eth.get_block("latest")["gasLimit"]
            #gas_limit = min(12_000_000, block_gas_limit)  # Ensure gas_limit fits the block limit
            ## Adjust the gas fees
            #pool_min_fee_cap = web3_instance.to_wei('25', 'gwei')  # Pool minimum fee cap
            #max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')  # Slightly increase priority fee for faster inclusion
            #max_fee_per_gas = max(pool_min_fee_cap, max_priority_fee_per_gas + web3_instance.to_wei('10', 'gwei'))
            #max_priority_fee_per_gas = 0
            #max_fee_per_gas = 50_000_000_000
            nonce = self.get_nonce(wallet_addr, network=network)

            tx_data = {
                "chain_id": chain_id,  # Use the chain ID from configuration
                "tx": {
                    "chain_id": hex(chain_id),
                    "gas": hex(gas_limit),
                    "maxFeePerGas": hex(max_fee_per_gas),
                    "maxPriorityFeePerGas": hex(max_priority_fee_per_gas),
                    "nonce": hex(nonce),
                    "to": transaction["to"],
                    "type": "0x2",
                    "value": hex(transaction["value"]),
                    "data": transaction.get("data", "0x")
                }
            }

            # Call the signing API
            cs_url = self.config_manager.get_nested_config_value("cs", "url")
            api_url = f"{cs_url}/v1/org/{encoded_org_id}/eth1/sign/{wallet_addr}"
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": f"{role_session_token}"  # Include the session token in the Authorization header
            }

            response = requests.post(api_url, json=tx_data, headers=headers)
            response.raise_for_status()  # Check for any HTTP errors

            if response.status_code != 200:
                raise ValueError(f"Signing API returned error: {response.json().get('error', 'Unknown error')}")

            # Extract the signed transaction from the response
            signed_tx = response.json().get("rlp_signed_tx")
            if not signed_tx:
                raise ValueError("Signed transaction not found in response")

            signed_tx_bytes = web3_instance.to_bytes(hexstr=signed_tx)

            # Send the signed transaction to the network
            tx_hash = web3_instance.eth.send_raw_transaction(signed_tx_bytes)
            tx_hash_hex = tx_hash.hex()

            # Ensure the prefix
            if not tx_hash_hex.startswith("0x"):
                tx_hash_hex = f"0x{tx_hash_hex}"

            # Create a row in the Event table with known fields
            Event.objects.create(
                contract_idx=contract_idx,  
                network=network,
                from_addr=wallet_addr,
                to_addr=transaction["to"],
                tx_hash=tx_hash_hex,
                event_type="TransactionSent",
                details="Pending",
                status="pending" 
            )

            # Add a timeout to wait for the transaction receipt (e.g., 120 seconds)
            tx_receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

            return tx_receipt

        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending request to signing API: {str(e)}")
            raise

        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            raise

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
            gas_limit = 10_000_000  # Reasonably high limit for large contracts

            # Use fixed gas fees for simplicity
            max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')  # Priority fee
            max_fee_per_gas = web3_instance.to_wei('100', 'gwei')  # Max fee per gas

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