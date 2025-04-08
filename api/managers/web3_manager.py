import logging
import os
import json
import requests
import urllib.parse

from eth_utils import keccak, to_checksum_address
from web3 import Web3, HTTPProvider
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

from api.models.event_model import Event
from api.utilities.logging import log_error, log_info, log_warning

class Web3Manager():

    ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
    _web3_instances = {}

    def __init__(self, context):
        self.logger = logging.getLogger(__name__)
        self.context = context

    def get_web3_instance(self, network):
        """Retrieve or create a Web3 instance for a given network """
        if network not in self._web3_instances:
            rpc_url = self._get_rpc_url(network)  
            log_info(self.logger, f"Retrieved rpc_url {rpc_url}")
            self._web3_instances[network] = self._initialize_web3_instance(rpc_url, network)

        return self._web3_instances[network]

    def _get_rpc_url(self, network):
        """Retrieve the RPC URL for the specified network from the configuration."""
        rpc_config = self.context.config_manager.get_rpc_url()
        if not isinstance(rpc_config, list):
            raise ValueError("'rpc' configuration is not a list.")
        rpc_entry = next((rpc for rpc in rpc_config if rpc.get("key") == network), None)
        if not rpc_entry:
            raise ValueError(f"RPC URL for network '{network}' not found in configuration.")
        return rpc_entry.get("value")

    def _initialize_web3_instance(self, rpc_url, network):
        """Initialize and configure a Web3 instance."""
        web3_instance = Web3(HTTPProvider(rpc_url))
        if not web3_instance.is_connected():
            raise ConnectionError(f"Failed to connect to the RPC for network '{network}'")

        if self.context.domain_manager.is_poa_chain(network):
            web3_instance.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

        log_info(self.logger, f"Web3 connection established for {network}")
        return web3_instance

    def get_web3_contract(self, contract_type, network):
        cache_key = self.context.cache_manager.get_contract_abi_cache_key(contract_type)
        abi = self.context.cache_manager.get(cache_key)

        if not abi:
            abi = self.load_abi(contract_type)
            self.context.cache_manager.set(cache_key, abi, timeout=None) 
            log_info(self.logger, f"Cached ABI for {contract_type}")

        log_info(self.logger, f"Retrieving web3_instance for network {network}")
        web3_instance = self.get_web3_instance(network)
        contract_address = self.context.config_manager.get_contract_address(contract_type)

        if not contract_address:
            raise ValueError("Contract address is missing in configuration")

        return web3_instance.eth.contract(abi=abi, address=contract_address)

    def get_nonce(self, wallet_addr, network):
        """Get the transaction nonce for a wallet."""
        web3_instance = self.get_web3_instance(network)
        return web3_instance.eth.get_transaction_count(to_checksum_address(wallet_addr))

    def get_checksum_address(self, wallet_addr):
        """Convert an address to checksum format."""
        return to_checksum_address(wallet_addr)

    def load_abi(self, contract_type):
        cache_key = self.context.cache_manager.get_contract_abi_cache_key(contract_type)
        abi = self.context.cache_manager.get(cache_key)

        if abi:
            return abi

        abi_file_path = os.path.join(os.path.dirname(__file__), f"../contract/abi/{contract_type}.json")

        if not os.path.exists(abi_file_path):
            log_error(self.logger, f"ABI file not found: {abi_file_path}")
            raise FileNotFoundError(f"ABI file not found: {abi_file_path}")

        try:
            with open(abi_file_path, "r") as abi_file:
                abi = json.load(abi_file)
                self.context.cache_manager.set(cache_key, abi, timeout=None)

                return abi

        except json.JSONDecodeError as e:
            log_error(self.logger, f"Failed to parse ABI JSON: {e}")
            raise
        except Exception as e:
            log_error(self.logger, f"Error loading ABI: {e}")
            raise

    def send_signed_transaction(self, transaction, wallet_addr, contract_type, contract_idx, network):
        web3_instance = self.get_web3_instance(network)
        wallet_addr = to_checksum_address(wallet_addr)
        chain_id = self.context.config_manager.get_chain_id(network)

        if not web3_instance.is_connected():
            log_error(self.logger, "Web3 instance is not connected")
            raise ConnectionError("Web3 instance is not connected")

        try:
            nonce = self.get_nonce(wallet_addr, network)

            tx = self._build_transaction(
                from_addr=wallet_addr,
                to_addr=transaction['to'],
                value=transaction["value"],
                data=transaction.get('data','0x'),
                nonce=nonce,
                chain_id=chain_id
            )

            gas_limit, max_fee_per_gas, max_priority_fee_per_gas = self._estimate_gas_fees(web3_instance, tx)

            log_info(self.logger, f"TX to send {tx}")
            log_info(self.logger, f"gas_limit: {gas_limit}")
            log_info(self.logger, f"max_fee_per_gas {max_fee_per_gas}")
            log_info(self.logger, f"max_priority_fee_per_gas {max_priority_fee_per_gas}")

            # Update tx with gas values
            tx['gas'] = gas_limit
            tx['maxFeePerGas'] = max_fee_per_gas
            tx['maxPriorityFeePerGas'] = max_priority_fee_per_gas

            signed_tx, error_code = self._sign_transaction({"chain_id": chain_id, "tx": self._hexify_tx(tx)}, wallet_addr)

            if signed_tx:
                tx_hash, tx_receipt = self._broadcast_transaction(web3_instance, signed_tx)
                tx_hash_hex = Web3.to_hex(tx_hash)

                if contract_type is not None and contract_idx is not None:
                    contract_release = self.context.config_manager.get_contract_release(contract_type)
                    self._log_event(transaction, tx_hash_hex, wallet_addr, contract_type, contract_idx, contract_release, network)

            elif error_code == 'MfaRequired':
                tx_receipt = 'MfaRequired'
            else:
                raise RuntimeError(f"Error broadcasting transaction with error code: {error_code}")

            return tx_receipt

        except Exception as e:
            log_error(self.logger, f"Error sending signed transaction: {e}")
            raise

    def send_contract_deployment(self, bytecode, wallet_addr, network):

        web3_instance = self.get_web3_instance(network)
        wallet_addr = to_checksum_address(wallet_addr)
        chain_id = self.context.config_manager.get_chain_id(network)

        if not web3_instance.is_connected():
            logging.error(f"Web3 instance is not connected to the {network} network.")
            raise ConnectionError("Web3 instance is not connected")

        try:
            nonce = web3_instance.eth.get_transaction_count(wallet_addr, "pending")
            
            # Set a manually high gas limit
            gas_limit = 10_000_000  # Reasonably high limit for large contracts
            max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')  # Priority fee
            max_fee_per_gas = web3_instance.to_wei('100', 'gwei')  # Max fee per gas

            log_info(self.logger, f"Deployment Details")
            log_info(self.logger, f"Wallet Address: {wallet_addr}")
            log_info(self.logger, f"Gas Limit: {gas_limit}")
            log_info(self.logger, f"maxFeePerGas: {max_fee_per_gas}")
            log_info(self.logger, f"maxPriorityFeePerGas: {max_priority_fee_per_gas}")
                
            tx = self._build_transaction(
                from_addr=wallet_addr,
                to_addr=None,
                value=0,
                data=bytecode,
                nonce=nonce,
                gas_limit=gas_limit,
                max_fee_per_gas=max_fee_per_gas,
                max_priority_fee_per_gas=max_priority_fee_per_gas,
                chain_id=chain_id
            )

            signed_tx, error_code = self._sign_transaction({"chain_id": chain_id, "tx": self._hexify_tx(tx)}, wallet_addr)

            if signed_tx:
                tx_hash, tx_receipt = self._broadcast_transaction(web3_instance, signed_tx)
            else:
                raise RuntimeError(f"Transaction failed with error code {error_code}")

            return tx_receipt

        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            raise


    def _estimate_gas_fees(self, web3_instance, transaction):

        """Estimate gas fees for a transaction."""
        estimated_gas = web3_instance.eth.estimate_gas({
            "from": transaction["from"],
            "to": transaction["to"],
            "from": transaction["from"],
            "data": transaction.get("data", "0x"),
            "value": transaction["value"],
        })

        log_info(self.logger, f"estimated gas: {estimated_gas}")

        block_gas_limit = web3_instance.eth.get_block("latest")["gasLimit"]
        gas_limit = min(estimated_gas, block_gas_limit)
        pool_min_fee_cap = web3_instance.to_wei('25', 'gwei')
        max_priority_fee_per_gas = web3_instance.to_wei('2', 'gwei')
        max_fee_per_gas = pool_min_fee_cap + web3_instance.to_wei('10', 'gwei')

        return gas_limit, max_fee_per_gas, max_priority_fee_per_gas

    def _sign_transaction(self, tx_data, wallet_addr):
        """Sign a transaction using the signing API."""
        cs_url = self.context.config_manager.get_cs_url()
        org_id = self.context.config_manager.get_cs_org_id()
        encoded_org_id = urllib.parse.quote(org_id, safe='')

        # used lower() to workaround a Cubesigner bug where it was not allowing me to submit
        # the transaction. remove the .lower() when this bug is resolved
        api_url = f"{cs_url}/v1/org/{encoded_org_id}/eth1/sign/{wallet_addr.lower()}"

        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "Authorization": self.context.secrets_manager.get_cs_role_session_token(),
        }

        response = requests.post(api_url, json=tx_data, headers=headers)

        response.raise_for_status()
        signed_tx = response.json().get("rlp_signed_tx")
        error_code = response.json().get("error_code")

        return signed_tx, error_code

    def _broadcast_transaction(self, web3_instance, signed_tx):
        """Broadcast the signed transaction to the network."""

        tx_hash = web3_instance.eth.send_raw_transaction(web3_instance.to_bytes(hexstr=signed_tx))
        tx_receipt = web3_instance.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        return tx_hash, tx_receipt

    def _log_event(self, transaction, tx_hash, wallet_addr, contract_type, contract_idx, contract_release, network):
        """ Log event associated with a particular contract"""

        try:
            Event.objects.create(
                contract_idx=contract_idx,
                contract_type=contract_type,
                contract_release=contract_release,
                network=network,
                from_addr=wallet_addr,
                to_addr=transaction["to"],
                tx_hash=tx_hash,
                event_type="TransactionSent",
                details="Pending",
                status="pending",
            )

        except Exception as e:
            logging.error(f"Error occurred: {str(e)}")
            raise

    def _build_transaction(self, from_addr, to_addr=None, value=0, data="0x", nonce=None, gas_limit=None, max_fee_per_gas=None, max_priority_fee_per_gas=None, chain_id=None):
        """Build a basic EIP-1559 transaction dict."""
        return {
            "from": from_addr,
            "nonce": nonce,
            "value": value,
            "to": to_addr,  # None for contract deployment
            "gas": gas_limit,
            "maxFeePerGas": max_fee_per_gas,
            "maxPriorityFeePerGas": max_priority_fee_per_gas,
            "type": "0x2",  # EIP-1559 transaction
            "data": data
        }

    def get_zero_address(self):
        return self.ZERO_ADDRESS

    def _hexify_tx(self, tx):
        """Convert int values in tx dict to hex strings."""
        return {k: (hex(v) if isinstance(v, int) else v) for k, v in tx.items()}

    def reset_web3_cache(self):
        """Clear all Web3-related caches."""
        for contract_type in self.context.domain_manager.get_contract_types():
            self.context.cache_manager.delete(self.context.cache_manager.get_contract_abi_cache_key(contract_type))
