import os

from django.core.management.base import BaseCommand
from django.conf import settings
from api.managers import SecretsManager, ConfigManager, Web3Manager

class Command(BaseCommand):
    help = 'Deploy a smart contract to the blockchain'

    def handle(self, *args, **kwargs):
        # Initialize Web3Manager
        web3_manager = Web3Manager()

        # Load secrets and config
        secrets_manager = SecretsManager()
        config_manager = ConfigManager()

        secrets = secrets_manager.load_keys()
        config = config_manager.load_config()

        # Network and wallet configuration
        network = "fizit"
        wallet_key = "Contract"

        # Fetch wallet address associated with "Contract"
        wallet_config = config.get("wallet_addr", [])
        wallet_address = next(
            (entry["value"] for entry in wallet_config if entry["key"] == wallet_key), None
        )

        if not wallet_address:
            raise ValueError(f"Wallet address for key '{wallet_key}' not found in configuration.")

        # Compile the contract
        contract_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'delivery.sol')
        abi, bytecode = self.compile_contract(contract_file_path)

        self.stdout.write(f"Bytecode length: {len(bytecode)}")

        # Save the ABI to a JSON file
        abi_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'delivery_abi.json')
        with open(abi_file_path, 'w') as abi_file:
            import json
            json.dump(abi, abi_file)

        # Deploy the contract using Web3Manager
        try:
            tx_receipt = web3_manager.send_contract_deployment(
                bytecode=bytecode,
                wallet_addr=wallet_address,
                network=network,
                abi=abi
            )

            self.stdout.write(f"tx_receipt: {tx_receipt}")

            # Log the deployed contract address
            # Output the AES key to stdout for manual handling
            self.stdout.write(self.style.SUCCESS(f"Contract deployed at address: {tx_receipt.contractAddress}"))
            self.stdout.write(self.style.SUCCESS(f"Reminder: Update Config"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to deploy the contract: {str(e)}"))

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