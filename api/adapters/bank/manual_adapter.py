import logging

from api.managers.app_context import AppContext
from api.interfaces.mixins import ResponseMixin
from api.utilities.logging import log_error, log_info, log_warning

class ManualAdapter(ResponseMixin):

    def __init__(self, context: AppContext):
        self.logger = logging.getLogger(__name__)

    def get_accounts(self):
        return []
    def get_recipients(self):
        return []
    def get_deposits(self):
        return []

    def make_payment(self, tx_hash, amount):
        return tx_hash
