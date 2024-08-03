import json
import os

_env_abi = None

def load_abi():
    global _env_abi
    python_path = os.environ['PYTHONPATH']

    if _env_abi is None:

        # Load contract ABI from file
        with open(os.path.join(python_path, "../truffle/build/contracts/Delivery.json")) as cf:
            _env_abi = json.load(cf)["abi"]

    return _env_abi