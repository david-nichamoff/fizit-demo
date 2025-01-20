import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from api.managers import SecretsManager, ConfigManager, Web3Manager
from api.models import Contract

class Command(BaseCommand):
    help = 'Deploy a smart contract to the blockchain'

    def handle(self, *args, **kwargs):
        # Initialize managers
        web3_manager = Web3Manager()
        secrets_manager = SecretsManager()
        config_manager = ConfigManager()

        # Load secrets and config
        secrets = secrets_manager.load_keys()
        config = config_manager.load_config()

        # Network and wallet configuration
        network = "fizit"
        wallet_key = "Transactor"

        # Fetch wallet address associated with "Contract"
        wallet_config = config.get("wallet_addr", [])
        wallet_address = next(
            (entry["value"] for entry in wallet_config if entry["key"] == wallet_key), None
        )

        if not wallet_address:
            raise ValueError(f"Wallet address for key '{wallet_key}' not found in configuration.")

        # Save the current contract address in a temporary variable
        current_contract_addr = config.get("contract_addr")
        if not current_contract_addr:
            raise ValueError("Current contract address not found in configuration.")

        self.stdout.write(f"Current contract address: {current_contract_addr}")

        # Compile the contract
        contract_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'delivery.sol')
        abi, bytecode = self.compile_contract(contract_file_path)

        self.stdout.write(f"Bytecode length: {len(bytecode)}")

        # Save the ABI to a JSON file
        abi_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'delivery_abi.json')
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

            new_contract_addr = tx_receipt.contractAddress
            self.stdout.write(f"New contract deployed at address: {new_contract_addr}")

            # Update smart contract history
            self.update_smart_contract_history(current_contract_addr, new_contract_addr)

            # Update config.json with the new contract address
            config_manager.update_config_value("contract_addr", new_contract_addr)

            self.stdout.write(self.style.SUCCESS("Config updated with new contract address."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to deploy the contract: {str(e)}"))

    def update_smart_contract_history(self, current_contract_addr, new_contract_addr):
        """Update smart contract history in the database."""
        # Set expiry date for the current contract
        try:
            current_contract = Contract.objects.get(contract_addr=current_contract_addr)
            current_contract.expiry_dt = timezone.now()
            current_contract.save()
            self.stdout.write(f"Updated expiry date for contract: {current_contract_addr}")
        except Contract.DoesNotExist:
            self.stdout.write(self.style.WARNING(f"Current contract {current_contract_addr} not found in history."))

        # Create a new entry for the new contract
        new_contract = Contract(
            contract_addr=new_contract_addr,
            created_dt= timezone.now()
        )
        new_contract.save()
        self.stdout.write(f"Created new smart contract entry for: {new_contract_addr}")

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
                    "delivery.sol": {
                        "content": contract_source_code
                    }
                },
                "settings": {
                    "optimizer": {
                        "enabled": True,  # Enable the optimizer
                        "runs": 200       # Set the optimization runs
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
        
        # Extract the first contract from the compilation result
        contract_name = list(compiled_contract["contracts"]["delivery.sol"].keys())[0]
        contract_data = compiled_contract["contracts"]["delivery.sol"][contract_name]

        # Extract ABI and bytecode
        abi = contract_data["abi"]
        bytecode = contract_data["evm"]["bytecode"]["object"]

        return abi, bytecode