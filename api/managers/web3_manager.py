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
    _web3_instance = None
    _web3_contract = None
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

    def get_web3_instance(self):
        """Get or create the Web3 instance."""
        if self._web3_instance is None:
            ava_rpc_url = self.config.get("ava_rpc")
            if not ava_rpc_url:
                raise ValueError("Avalanche RPC URL is missing")

            try:
                web3_provider_url = ava_rpc_url
                self._web3_instance = Web3(HTTPProvider(web3_provider_url))

                # Add the middleware to handle Proof of Authority chains
                self._web3_instance.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
                
                if self._web3_instance.is_connected():
                    print("Web3 connection successful")
                else:
                    raise ConnectionError("Failed to connect to Avalanche RPC")
            except Exception as e:
                print(f"Error connecting to Avalanche RPC: {e}")
                raise

        return self._web3_instance

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
    
    def get_web3_contract(self):
        """Get or create the Web3 contract instance."""
        if self._web3_contract is None:
            web3_instance = self.get_web3_instance()
            contract_address = self.config.get("contract_addr")

            if not contract_address:
                raise ValueError("Contract address is missing in configuration")

            self._web3_contract = web3_instance.eth.contract(
                abi=self.load_abi(),
                address=contract_address
            )
            print("Contract loaded")

        return self._web3_contract

    def get_nonce(self, wallet_addr):
        web3_instance = self.get_web3_instance()
        return web3_instance.eth.get_transaction_count(wallet_addr)

    def send_signed_transaction(self, transaction, wallet_addr):
        web3_instance = self.get_web3_instance()

        # Check if web3 is connected before proceeding
        if not web3_instance.is_connected():
            logging.error("Web3 instance is not connected to the Avalanche network.")
            raise ConnectionError("Web3 instance is not connected")

        org_id = self.config.get("cs_org_id")
        encoded_org_id = urllib.parse.quote(org_id, safe='')

        # Retrieve the session token from config or environment
        session_token = self.keys.get("session_token")
        if not session_token:
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
            api_url = f"{self.config.get('cs_url')}/v1/org/{encoded_org_id}/eth1/sign/{wallet_addr}"
            headers = {
                "Content-Type": "application/json",
                "accept": "application/json",
                "Authorization": f"{session_token}"  # Include the session token in the Authorization header
            }

            response = requests.post(api_url, json=tx_data, headers=headers)
            response.raise_for_status()  # Check for any HTTP errors

            # Extract the signed transaction from the response
            signed_tx = response.json().get("rlp_signed_tx")
            if not signed_tx:
               raise ValueError("Signed transaction not found in response")

            signed_tx_bytes = web3_instance.to_bytes(hexstr=signed_tx)

            # For debugging purposes, print the decode_d transaction
            #self._decode_signed_transaction(signed_tx_bytes, "CubeSigner")

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

    """
    def send_signed_transaction(self, transaction, wallet_addr):
        web3_instance = self.get_web3_instance()
        private_key = self.keys.get("wallet_key")

        if not private_key:
            raise ValueError("Private key is missing in the keys configuration")

        try:
            signed_tx = web3_instance.eth.account.sign_transaction(transaction, private_key=private_key)

            # For debugging purposes, print the decode_d transaction
            self._decode_signed_transaction(signed_tx.raw_transaction, "Core Wallet")

            send_tx = web3_instance.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_receipt = web3_instance.eth.wait_for_transaction_receipt(send_tx)

            return tx_receipt

        except Exception as e:
            logging.error(f"Error sending transaction: {str(e)}")
            raise
    """

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