import requests
import os
import datetime
import time
import requests
import babel.numbers
import decimal

import web3
from web3 import Web3

src_dict = {}

# Get api_key and ids for each src
with open("./src_bus_id.txt","r") as fin:
    lines = fin.readlines()

for line in lines:
    src_id, api_key, src_code, src_wallet = line.split(',')
    src_dict[src_id] = (api_key, src_code.strip(), src_wallet.strip())

# Open a connection to Avalanche, get contract and abi
with open("./ava_rpc.txt","r") as fin:
    ava_rpc = fin.read()

with open("./ava_api_key.txt","r") as fin:
    ava_api_key = fin.read()

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

for src in src_dict:
    result = contract.functions.getTickets(src_dict[src][2]).call()
    print(result)
