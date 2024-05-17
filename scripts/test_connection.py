from web3 import Web3,HTTPProvider
from web3.middleware import geth_poa_middleware

rpc_url_dev = 'https://subnets.avacloud.io/f8b4d7c7-e374-4d79-abdd-e2e3ba007481'
rpc_url_test = 'https://subnets.avax.network/fizit/testnet/rpc'

api_key_dev = 'ac_7QCVWONF_CBHlfTfm0ltnFei7u1GOUwblk5KK94qW7l2DUHEbb30wPKAyOU3cygqf1QnW1oz_MLRCuWYAaG-cA'
api_key_test = 'ac_pX0UXQtf00XTdA3C9ZVRRcFj9cGo5y95L0en5dgHZF3obuAXZ0cg-MUxRfRFe5PvlngjBZDFI7_QJ5XzNRhzbw'
      
web3_provider_url = f"{rpc_url_dev}"
print (web3_provider_url)
        
_web3_instance = Web3(HTTPProvider(web3_provider_url))
_web3_instance.middleware_onion.inject(geth_poa_middleware, layer=0)
            
if _web3_instance.is_connected():
    print("Connection successful")
else:
    print("Connection failed")