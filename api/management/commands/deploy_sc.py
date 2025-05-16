import os
import json
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone

from api.utilities.bootstrap import build_app_context
from api.models import SmartContract

class Command(BaseCommand):
    help = 'Deploy a smart contract to the blockchain'

    def add_arguments(self, parser):
        parser.add_argument(
            '--contract_type',
            type=str,
            required=True,
            help='The type of contract to deploy (e.g., purchase, sale, advance)',
        )

    def handle(self, *args, **kwargs):
        contract_type = kwargs['contract_type']
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

        # Initialize managers
        w3 = self.context.web3_manager.get_web3_instance(network="fizit")

        # Ensure Web3 connection
        if not w3.is_connected():
            raise ConnectionError("Web3 is not connected. Check your RPC URL and node status.")

        # Print chain ID to verify network
        chain_id = w3.eth.chain_id
        self.stdout.write(f"Connected to network with Chain ID: {chain_id}")

        # Validate contract_type
        if contract_type not in self.context.domain_manager.get_contract_types():
            raise ValueError(f"Invalid contract_type '{contract_type}'.")

        self.stdout.write(f"Using contract type: {contract_type}")

        # Network and wallet configuration
        network = "fizit"
        wallet_key = "admin"

        # Fetch wallet address associated with "Admin"
        wallet_address = self.context.config_manager.get_wallet_address(wallet_key)
        wallet_address = w3.to_checksum_address(wallet_address)

        if not wallet_address:
            raise ValueError(f"Wallet address for key '{wallet_key}' not found in configuration.")

        self.stdout.write(f"Using wallet address: {wallet_address}")

        # Check wallet balance
        balance = w3.eth.get_balance(wallet_address)
        self.stdout.write(f"Wallet balance: {w3.from_wei(balance, 'ether')} FIZIT")

        current_contract_addr = self.context.config_manager.get_contract_address(contract_type)
        current_contract_release = self.context.config_manager.get_contract_release(contract_type)

        if current_contract_addr:
            self.stdout.write(f"Current contract address: {current_contract_addr}")
        else:
            self.stdout.write("No current contract address found — this is the first deployment.")

        if current_contract_release is None:
            self.stdout.write("No current contract release found — initializing to 0.")
            current_contract_release = 0
        else:
            self.stdout.write(f"Current contract release: {current_contract_release}")
            self.stdout.write(f"Current contract address: {current_contract_addr}")
            self.stdout.write(f"Current contract release: {current_contract_release}")

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
            tx_receipt = self.context.web3_manager.send_contract_deployment(
                bytecode=bytecode,
                wallet_addr=wallet_address,
                network=network
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

            new_contract_release = current_contract_release + 1

            # Verify contract exists at the deployed address
            deployed_code = w3.eth.get_code(new_contract_addr)
            if deployed_code.hex() == "0x":
                raise ValueError("Contract was deployed, but no bytecode found at this address!")

            self.stdout.write(f"Contract successfully deployed and verified at {new_contract_addr}")
            self.stdout.write(f"Reload cache!")

            # Update smart contract history
            self.update_smart_contract_history(current_contract_addr, new_contract_addr, new_contract_release, contract_type)

            # Update config.json with the new contract address
            self.update_config(contract_type, new_contract_addr, new_contract_release)

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to deploy the contract: {str(e)}"))

    def update_smart_contract_history(self, current_contract_addr, new_contract_addr, new_contract_release, contract_type):
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
            contract_release=new_contract_release,
            contract_type=contract_type,
            created_dt=timezone.now()
        )
        new_contract.save()
        self.stdout.write(f"Created new smart contract entry for: {new_contract_addr} for type {contract_type}")

    def update_config(self, contract_type, new_contract_addr, new_contract_release):
        """Update the contract address in config.json for the given contract_type."""
        self.context.config_manager.update_contract_address(contract_type, new_contract_addr, new_contract_release)

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