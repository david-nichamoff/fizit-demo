import os
from django.core.management.base import BaseCommand
from django.conf import settings
from solcx import compile_source


class Command(BaseCommand):
    help = 'Calculate the bytecode size of a Solidity smart contract'

    def handle(self, *args, **kwargs):
        # Path to the Solidity source code
        contract_file_path = os.path.join(settings.BASE_DIR, 'api', 'contract', 'delivery.sol')

        if not os.path.exists(contract_file_path):
            self.stderr.write(f"Contract file not found: {contract_file_path}")
            return

        try:
            # Read the contract source code
            with open(contract_file_path, 'r') as contract_file:
                contract_source_code = contract_file.read()

            # Compile the contract
            compiled_contract = compile_source(
                contract_source_code,
                output_values=["abi", "bin"]
            )

            # Extract the bytecode
            contract_name = list(compiled_contract.keys())[0]
            bytecode = compiled_contract[contract_name]["bin"]

            # Calculate the bytecode size
            bytecode_size = len(bytecode) // 2  # Each byte is represented by 2 hex characters

            # Output the bytecode size
            self.stdout.write(f"Smart contract bytecode size: {bytecode_size} bytes")

            # Check if the size exceeds the EVM limit
            if bytecode_size > 24576:
                self.stderr.write(
                    "WARNING: Bytecode size exceeds the EVM limit of 24,576 bytes. Deployment will fail."
                )
            else:
                self.stdout.write("Bytecode size is within the EVM limit.")
        except Exception as e:
            self.stderr.write(f"Failed to calculate smart contract size: {str(e)}")