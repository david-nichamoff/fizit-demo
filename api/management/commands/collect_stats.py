import logging
import time
from datetime import datetime, timezone
from eth_abi import decode
from decimal import Decimal

from django.core.management.base import BaseCommand

from api.utilities.bootstrap import build_app_context
from api.utilities.logging import log_error, log_info, log_warning
from api.operations import CsrfOperations, ContractOperations, TransactionOperations

class Command(BaseCommand):
    help = 'Listen to contract events and update them in the database'

    def handle(self, *args, **kwargs):
        self.context = build_app_context()
        self.logger = logging.getLogger(__name__)

        headers = {
            'Authorization': f"Api-Key {self.context.secrets_manager.get_master_key()}",
            'Content-Type': 'application/json',
        }

        base_url = self.context.config_manager.get_base_url()
        csrf_ops = CsrfOperations(headers, self.context.config_manager.get_base_url())
        csrf_token = csrf_ops.get_csrf_token()

        self.contract_ops = ContractOperations(headers, base_url, csrf_token)
        self.transaction_ops = TransactionOperations(headers, base_url, csrf_token)

        while True:

            # Sleep upon launch so it doesn't kick off immediately
            time.sleep(self.context.config_manager.get_stats_sleep_time()) 

            stats = {
                "total_advance_amt": 0,
                "total_transactions": 0
            }

            try:
                contract_types = self.context.domain_manager.get_contract_types()
                for contract_type in contract_types:
                    count_response = self.contract_ops.get_count(contract_type)
                    contract_count = count_response['count']

                    log_info(self.logger, f"Retrieved {contract_count} contracts for contract_type {contract_type}")

                    for contract_idx in range(0, contract_count):

                        transactions = self.transaction_ops.get_transactions(contract_type, contract_idx)
                        for transaction in transactions:
                            advance_pay_amt = Decimal(transaction.get("advance_pay_amt", 0))
                            log_info(self.logger, f"Contract: {contract_type}:{contract_idx} Transact Amount: {advance_pay_amt}")

                            if advance_pay_amt > 0:
                                stats['total_transactions'] += 1 
                                stats['total_advance_amt'] += advance_pay_amt

            except Exception as e:
                log_error(self.logger, f"Error processing stats")

            cache_key = self.context.cache_manager.get_stats_cache_key()
            self.context.cache_manager.set(cache_key, {
                'total_advance_amt': round(stats['total_advance_amt']),
                'total_transactions': stats['total_transactions']
            })

            log_info(self.logger, f"Total advance value: {stats['total_advance_amt']}")
            log_info(self.logger, f"Total transactions: {stats['total_transactions']}")

