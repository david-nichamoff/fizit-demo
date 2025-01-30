import os
import json
from datetime import datetime

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from api.secrets import SecretsManager
from api.config import ConfigManager
from api.web3 import Web3Manager
from api.registry import RegistryManager
from api.models import SmartContract

class Command(BaseCommand):
    help = 'Deploy a smart contract to the blockchain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contract_type',
            type=str,
            required=True,
            help='The type of contract to deploy (e.g., ticketing, advance, delivery)',
        )

    def handle(self, *args, **kwargs):
        contract_type = kwargs['contract_type']

        # Initialize managers
        web3_manager = Web3Manager()
        w3 = web3_manager.get_web3_instance(network="fizit")

        secrets_manager = SecretsManager()
        config_manager = ConfigManager()
        registry_manager = RegistryManager()

        # Ensure Web3 connection
        if not w3.is_connected():
            raise ConnectionError("Web3 is not connected. Check your RPC URL and node status.")

        # Print chain ID to verify network
        chain_id = w3.eth.chain_id
        self.stdout.write(f"Connected to network with Chain ID: {chain_id}")

        # Validate contract_type
        if contract_type not in registry_manager.get_contract_types():
            raise ValueError(f"Invalid contract_type '{contract_type}'.")

        self.stdout.write(f"Using contract type: {contract_type}")

        # Network and wallet configuration
        network = "fizit"
        wallet_key = "Admin"

        # Fetch wallet address associated with "Admin"
        wallet_address = config_manager.get_wallet_address(wallet_key)
        wallet_address = w3.to_checksum_address(wallet_address)

        if not wallet_address:
            raise ValueError(f"Wallet address for key '{wallet_key}' not found in configuration.")

        self.stdout.write(f"Using wallet address: {wallet_address}")

        # Check wallet balance
        balance = w3.eth.get_balance(wallet_address)
        self.stdout.write(f"Wallet balance: {w3.from_wei(balance, 'ether')} FIZIT")

        # Save the current contract address in a temporary variable
        current_contract_addr = config_manager.get_contract_address(contract_type)
        if not current_contract_addr:
            raise ValueError(f"Current contract address for type '{contract_type}' not found in configuration.")

        self.stdout.write(f"Current contract address: {current_contract_addr}")

        # Check nonce before deployment
        nonce = w3.eth.get_transaction_count(wallet_address)
        self.stdout.write(f"Wallet nonce before deployment: {nonce}")

        # Load Solidity contract source based on contract_type
        contract_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'source', f"{contract_type}.sol")
        abi, bytecode = self.compile_contract(contract_file_path)

        self.stdout.write(f"Compiled contract bytecode length: {len(bytecode)}")

        if not bytecode:
            raise ValueError("Contract bytecode is empty. Compilation failed.")

        # Save ABI to a contract-type specific location
        abi_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'abi', f"{contract_type}.json")
        with open(abi_file_path, 'w') as abi_file:
            json.dump(abi, abi_file)

        # Deploy the contract using Web3Manager
        try:
            tx_receipt = web3_manager.send_contract_deployment(
                bytecode=bytecode,
                wallet_addr=wallet_address,
                network=network,
                abi=abi
            )

            # Extract transaction hash from the receipt
            tx_hash = tx_receipt.transactionHash.hex()
            self.stdout.write(f"Deployment TX sent: {tx_hash}")

            # Wait for transaction to be mined
            import time
            self.stdout.write("Waiting for deployment transaction to be mined...")
            time.sleep(5)  # Wait a few seconds

            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            if not tx_receipt:
                self.stdout.write("Deployment transaction still pending...")
                return

            self.stdout.write(f"Deployment TX confirmed in block {tx_receipt.blockNumber}")

            # Extract deployed contract address
            new_contract_addr = tx_receipt.contractAddress
            self.stdout.write(f"New contract deployed at address: {new_contract_addr}")

            # Verify contract exists at the deployed address
            deployed_code = w3.eth.get_code(new_contract_addr)
            if deployed_code.hex() == "0x":
                raise ValueError("Contract was deployed, but no bytecode found at this address!")

            self.stdout.write(f"Contract successfully deployed and verified at {new_contract_addr}")

            # Update smart contract history
            self.update_smart_contract_history(current_contract_addr, new_contract_addr, contract_type)

            # Update config.json with the new contract address
            self.update_config(contract_type, new_contract_addr)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to deploy the contract: {str(e)}"))

    def update_smart_contract_history(self, current_contract_addr, new_contract_addr, contract_type):
        """Update smart contract history in the database."""
        # Set expiry date for the current contract
        try:
            current_contract = SmartContract.objects.get(contract_addr=current_contract_addr)
            current_contract.expiry_dt = timezone.now()
            current_contract.save()
            self.stdout.write(f"Updated expiry date for contract: {current_contract_addr}")
        except SmartContract.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Current contract {current_contract_addr} not found in history."))

        # Create a new entry for the new contract
        new_contract = SmartContract(
            contract_addr=new_contract_addr,
            contract_type=contract_type,
            created_dt=timezone.now()
        )
        new_contract.save()
        self.stdout.write(f"Created new smart contract entry for: {new_contract_addr} for type {contract_type}")

    def update_config(self, contract_type, new_contract_addr):
        """Update the contract address in config.json for the given contract_type."""
        config_manager = ConfigManager()
        config_manager.update_contract_address(contract_type, new_contract_addr)

    # Compile the Solidity contract
    def compile_contract(self, contract_file_path):
        with open(contract_file_path, "r") as file:
            contract_source_code = file.read()

        from solcx import compile_standard, install_solc, set_solc_version

        # Install and set the correct compiler version
        install_solc("0.8.0")
        set_solc_version("0.8.0")

        # Compile the Solidity source code with optimizer settings
        try:
            compiled_contract = compile_standard({
                "language": "Solidity",
                "sources": {
                    os.path.basename(contract_file_path): {
                        "content": contract_source_code
                    }
                },
                "settings": {
                    "optimizer": {
                        "enabled": True,  # Enable optimizer
                        "runs": 1000
                    },
                    "outputSelection": {
                        "*": {
                            "*": ["abi", "evm.bytecode.object"]
                        }
                    }
                }
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to compile the contract: {str(e)}"))
            raise

        contract_name = list(compiled_contract["contracts"][os.path.basename(contract_file_path)].keys())[0]
        contract_data = compiled_contract["contracts"][os.path.basename(contract_file_path)][contract_name]

        return contract_data["abi"], contract_data["evm"]["bytecode"]["object"]