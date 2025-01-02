from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware

def get_block_gas_limit(rpc_url):
    """
    Connect to the blockchain via RPC and return the current block gas limit.
    """
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

    if web3.is_connected():
        print("Connected to the blockchain.")
        block_gas_limit = web3.eth.get_block("latest")["gasLimit"]
        return block_gas_limit
    else:
        raise ConnectionError("Failed to connect to the blockchain.")

# Example usage
RPC_URL = "https://subnets.avacloud.io/d3cba7f9-84c5-4bdd-a708-c5691bf9dee4"
CONTRACT_ADDRESS = "0x8C19238b1CE3937a98c5f0759374686a38E64461"

try:
    block_gas_limit = get_block_gas_limit(RPC_URL)
    print(f"Block gas limit: {block_gas_limit}")
except Exception as e:
    print(f"Error: {e}")