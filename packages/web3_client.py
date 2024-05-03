from web3 import Web3
from web3.middleware import geth_poa_middleware

import env_var
env_var = env_var.get_env()

_web3_instance = None
_web3_contract = None

def get_web3_instance():
    global _web3_instance
    if _web3_instance is None:
        # Open a connection to Avalanche, get contract and abi
        _web3_instance = Web3(Web3.HTTPProvider(env_var["ava_rpc"] + "/" + env_var["ava_api_key"]))
        _web3_instance.middleware_onion.inject(geth_poa_middleware, layer=0)
        print ("Connection successful") if _web3_instance.is_connected() else print ("Connection failed")
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