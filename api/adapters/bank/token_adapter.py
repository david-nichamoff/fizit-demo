import logging
from decimal import Decimal
from eth_utils import to_checksum_address

from api.managers import Web3Manager, SecretsManager, ConfigManager

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
            self.w3_manager = Web3Manager()
            self.w3 = self.w3_manager.get_web3_instance()

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Prevent reinitialization

    def make_payment(self, funder_wallet, recipient_wallet, token_name, amount):
        """Initiate a token payment from the funder wallet to the recipient wallet."""
        try:
            funder_wallet = to_checksum_address(funder_wallet)
            recipient_wallet = to_checksum_address(recipient_wallet)

            # Retrieve token contract address and ABI from configuration
            token_config = self.config.get(f"token_{token_name.lower()}", None)
            if not token_config:
                error_message = f"Token configuration for {token_name} not found."
                self.logger.error(error_message)
                return False, error_message

            token_contract_address = token_config['address']
            token_contract_abi = token_config['abi']

            # Load token contract
            token_contract = self.w3.eth.contract(address=token_contract_address, abi=token_contract_abi)

            # Convert amount to the smallest unit of the token (e.g., wei for ERC-20)
            decimals = token_contract.functions.decimals().call()
            smallest_unit_amount = int(Decimal(amount) * (10 ** decimals))

            # Build the transaction
            nonce = self.w3.eth.get_transaction_count(funder_wallet)
            transaction = token_contract.functions.transfer(
                recipient_wallet, smallest_unit_amount
            ).build_transaction({
                'from': funder_wallet,
                'nonce': nonce,
                'gas': self.config.get('gas_limit', 200000),
                'gasPrice': self.w3.eth.gas_price,
            })

            # Sign the transaction
            private_key = self.secrets_manager.get_private_key(funder_wallet)
            signed_tx = self.w3.eth.account.sign_transaction(transaction, private_key)

            # Send the transaction
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)

            # Wait for receipt
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            if tx_receipt['status'] == 1:
                self.logger.info(f"Token payment successful. TX hash: {tx_hash.hex()}")
                return True, None
            else:
                error_message = f"Token payment failed. TX hash: {tx_hash.hex()}"
                self.logger.error(error_message)
                return False, error_message

        except Exception as e:
            error_message = f"Unexpected error during token payment: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
