from web3 import Web3,HTTPProvider
from web3.middleware import geth_poa_middleware

import packages.load_keys as load_keys
import packages.load_config as load_config
import packages.load_abi as load_abi

keys = load_keys.load_keys()
config = load_config.load_config()
abi = load_abi.load_abi()

_web3_instance = None
_web3_contract = None

def get_web3_instance():
    global _web3_instance
    if _web3_instance is None:
        
        if not config["ava_rpc"]:
            raise ValueError("Avalanche RPC URL is missing")
        
        web3_provider_url = f"{config["ava_rpc"]}"
        
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
        _web3_contract = _web3_instance.eth.contract(abi=abi,address=config["contract_addr"])
        print ("Contract loaded")

    return _web3_contract

def get_tx_receipt(call_function):

    signed_tx = _web3_instance.eth.account.sign_transaction(call_function, private_key=keys["wallet_key"])
    send_tx = _web3_instance.eth.send_raw_transaction(signed_tx.rawTransaction)
    tx_receipt = _web3_instance.eth.wait_for_transaction_receipt(send_tx)

    return tx_receipt