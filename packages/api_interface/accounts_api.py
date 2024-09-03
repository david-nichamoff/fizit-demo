import logging
import adapter.bank.mercury

import packages.load_web3 as load_web3
import packages.load_config as load_config

config = load_config.load_config()

w3 = load_web3.get_web3_instance()
w3_contract = load_web3.get_web3_contract()

logger = logging.getLogger(__name__)

def get_accounts(bank):
    if bank == "mercury":  
        return adapter.bank.mercury.get_accounts()
    else:
        error_message = f"Unsupported bank: {bank}"
        logger.error(error_message)
        raise ValueError(error_message)

def get_recipients(bank):
    if bank == "mercury":
        return adapter.bank.mercury.get_recipients()
    else:
        error_message = f"Unsupported bank: {bank}"
        logger.error(error_message)
        raise ValueError(error_message)