import os
import logging

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

        # Save the ABI to a JSON file
        abi_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'delivery_abi.json')
        with open(abi_file_path, 'w') as abi_file:
            import json
            json.dump(abi, abi_file)

        # Deploy the contract using Web3Manager
        try:
            constructor_args = []  # Default empty list for constructor arguments

            if abi:
                constructor_abi = next((item for item in abi if item.get("type") == "constructor"), None)
                logging.info(f"constructor_abi {constructor_abi}")

                if constructor_abi and "inputs" in constructor_abi and constructor_abi["inputs"]:
                    logging.info(f"Constructor inputs expected: {constructor_abi['inputs']}")
                    raise ValueError("Constructor arguments are required but not provided.")
            
            # Deploy contract with or without constructor arguments
            tx_receipt = web3_manager.send_contract_deployment(
                bytecode=bytecode,
                constructor_args=constructor_args,  
                wallet_addr=wallet_address,
                contract_idx=None,  
                network=network,
                abi=abi
            )
            # Log the deployed contract address
            logging.info(f"Contract deployed at address: {tx_receipt.contractAddress}")
        except Exception as e:
            logging.exception(f"Failed to deploy the contract: {str(e)}")

    # Compile the Solidity contract
    def compile_contract(self, contract_file_path):
        with open(contract_file_path, "r") as file:
            contract_source_code = file.read()

        from solcx import compile_standard

        # Compile the Solidity source code with optimizer settings
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

        # Extract the first contract from the compilation result
        contract_name = list(compiled_contract["contracts"]["delivery.sol"].keys())[0]
        contract_data = compiled_contract["contracts"]["delivery.sol"][contract_name]

        # Extract ABI and bytecode
        abi = contract_data["abi"]
        bytecode = contract_data["evm"]["bytecode"]["object"]

        return abi, bytecode