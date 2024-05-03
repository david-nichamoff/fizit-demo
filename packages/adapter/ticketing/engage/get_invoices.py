import requests
import os
import datetime
import time
import requests
import babel.numbers
import decimal

import web3
from web3 import Web3

dest_dict = {}

# Get codes for each dest
with open("./dest_bus_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    dest_id, dest_code, dest_wallet = line.split(',')
    dest_dict[dest_id] =  (dest_code, dest_wallet.strip())

# Open a connection to Avalanche, get contract and abi
with open("./ava_rpc.txt","r") as fin:
    ava_rpc = fin.read()

with open("./ava_api_key.txt","r") as fin:
    ava_api_key = fin.read()

with open("./fizit_addr.txt","r") as fin:
    fizit_addr = fin.read()

w3 = Web3(Web3.HTTPProvider(ava_rpc + "/" + ava_api_key))

if w3.is_connected():
    print("Connection successful")
else:
    print ("Connection failed")

with open("./engage_contract_addr.txt","r") as fin:
    contract_addr = fin.read().strip()

with open("./engage_abi.txt","r") as fin:
    abi = fin.read()

contract=w3.eth.contract(abi=abi,address=contract_addr)

for dest in dest_dict:
    result = contract.functions.getInvoices(dest_dict[dest][1]).call()
    print(result)
