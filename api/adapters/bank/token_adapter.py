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
            self.w3 = self.w3_manager.get_web3_instance(network="avalanche")

            self.logger = logging.getLogger(__name__)
            self.initialized = True  # Prevent reinitialization

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