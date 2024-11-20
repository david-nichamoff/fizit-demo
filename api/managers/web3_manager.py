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

    def load_abi(self):
        """Load the contract ABI from file."""
        if self._abi is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            abi_file_path = os.path.join(current_dir, '../../truffle/build/contracts/Delivery.json')

            if not os.path.exists(abi_file_path):
                raise FileNotFoundError(f"ABI file not found: {abi_file_path}")

            with open(abi_file_path) as abi_file:
                self._abi = json.load(abi_file)["abi"]

        return self._abi

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

    def send_signed_transaction(self, transaction, wallet_addr):
            web3_instance = self.get_web3_instance()

            # Check if web3 is connected before proceeding
            if not web3_instance.is_connected():
                logging.error("Web3 instance is not connected to the Avalanche network.")
                raise ConnectionError("Web3 instance is not connected")

            org_id = self.config_manager.get_nested_config_value("cs", "org_id")
            encoded_org_id = urllib.parse.quote(org_id, safe='')

            # Retrieve the session token from config or environment
            role_session_token = self.keys.get("role_session_token")
            if not role_session_token:
                raise ValueError("Session token is missing in the configuration")

            try:

                # Estimate gas
                estimated_gas = web3_instance.eth.estimate_gas(transaction)
                max_priority_fee_per_gas = 0
                max_fee_per_gas = 50000000000

                tx_data = {
                    "chain_id": self.config.get("chain_id"),
                    "tx": {
                        "chain_id": hex(int(self.config.get("chain_id"))),
                        "gas": hex(estimated_gas),
                        "maxFeePerGas": hex(max_fee_per_gas),
                        "maxPriorityFeePerGas": hex(max_priority_fee_per_gas),
                        "nonce": hex(transaction["nonce"]),
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

                # Extract the signed transaction from the response
                signed_tx = response.json().get("rlp_signed_tx")
                if not signed_tx:
                    raise ValueError("Signed transaction not found in response")

                signed_tx_bytes = web3_instance.to_bytes(hexstr=signed_tx)

                # Send the signed transaction to the Ethereum network
                tx_hash = web3_instance.eth.send_raw_transaction(signed_tx_bytes)

                # Add a timeout to wait for the transaction receipt (e.g., 120 seconds)
                tx_receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

                return tx_receipt

            except requests.exceptions.RequestException as e:
                logging.error(f"Error sending request to signing API: {str(e)}")
                raise

            except Exception as e:
                logging.error(f"Error occurred: {str(e)}")
                raise

    def _decode_signed_transaction(self, signed_tx_raw, source="Core Wallet"):
        logging.info(f"[{source}] EIP-1559 transaction detected")
        decoded_tx = rlp.decode(signed_tx_raw[1:])
        decoded_tx_hexbytes = [HexBytes(item) if isinstance(item, bytes) else item for item in decoded_tx]

        # Log specific fields to compare
        logging.info(f"[{source}] Nonce: {decoded_tx_hexbytes[0].hex()}")
        logging.info(f"[{source}] Max Fee Per Gas: {decoded_tx_hexbytes[3].hex()}")
        logging.info(f"[{source}] Max Priority Fee Per Gas: {decoded_tx_hexbytes[4].hex()}")
        logging.info(f"[{source}] Recipient Address: {decoded_tx_hexbytes[5].hex()}")
        logging.info(f"[{source}] Transaction Data: {decoded_tx_hexbytes[6].hex()}")
        logging.info(f"[{source}] Full Transaction: {decoded_tx_hexbytes}")