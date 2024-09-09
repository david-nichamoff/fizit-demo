import json
import os
from web3 import Web3, HTTPProvider
from web3.middleware import geth_poa_middleware

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
                self._web3_instance.middleware_onion.inject(geth_poa_middleware, layer=0)
                
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

    def get_tx_receipt(self, call_function):
        """Sign and send a transaction, then return the transaction receipt."""
        web3_instance = self.get_web3_instance()
        private_key = self.keys.get("wallet_key")

        if not private_key:
            raise ValueError("Private key is missing in the keys configuration")

        signed_tx = web3_instance.eth.account.sign_transaction(call_function, private_key=private_key)
        send_tx = web3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
        tx_receipt = web3_instance.eth.wait_for_transaction_receipt(send_tx)

        return tx_receipt