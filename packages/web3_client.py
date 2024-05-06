from web3 import Web3,HTTPProvider
from web3.middleware import geth_poa_middleware

import env_var
env_var = env_var.get_env()

_web3_instance = None
_web3_contract = None

def get_web3_instance():
    global _web3_instance
    if _web3_instance is None:
        rpc_url = env_var.get("ava_rpc")
        api_key = env_var.get("ava_api_key")
        
        if not rpc_url or not api_key:
            raise ValueError("Avalanche RPC URL or API key is missing")
        
        web3_provider_url = f"{rpc_url}"
        
        try:
            _web3_instance = Web3(HTTPProvider(web3_provider_url))
            _web3_instance.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # Check connection status by trying to get the block number
            if _web3_instance.is_connected():
                print("Connection successful")
            else:
                print("Connection failed")
        except Exception as e:
            print(f"Error connecting to Avalanche RPC: {e}")
            raise
    
    return _web3_instance

def get_web3_contract():
    global _web3_contract
    if _web3_contract is None:
        _web3_contract = _web3_instance.eth.contract(abi=env_var["contract_abi"],address=env_var["contract_addr"])
        print ("Contract loaded")
    return _web3_contract

def get_tx_receipt(call_function):
    signed_tx = _web3_instance.eth.account.sign_transaction(call_function, private_key=env_var["wallet_key"])
    send_tx = _web3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = _web3_instance.eth.wait_for_transaction_receipt(send_tx)
    return tx_receipt

