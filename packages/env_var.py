import json
import os

_env_var = None

def get_env():
    global _env_var
    python_path = os.environ['PYTHONPATH']

    print ("Loading env")

    if _env_var is None:
        with open(python_path + "/../config/private_keys.json") as cf:
            _env_var = json.load(cf)
        with open(python_path + "/../config/public_env.json") as cf:
            _env_var.update(json.load(cf))
        with open(python_path + "/../truffle/build/contracts/Delivery.json") as cf:
            _env_var["contract_abi"] = json.load(cf)["abi"]

    print (_env_var)
    return _env_var