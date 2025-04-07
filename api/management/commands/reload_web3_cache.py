import logging
from django.core.management.base import BaseCommand
from api.managers.web3_manager import Web3Manager

class Command(BaseCommand):
    help = "Clear and reload Web3-related caches."

    def handle(self, *args, **kwargs):
        logger = logging.getLogger(__name__)

        try:
            web3_manager = Web3Manager()
            web3_manager.reset_web3_cache()
            self.stdout.write(self.style.SUCCESS("✅ Web3 cache successfully reset."))
        except Exception as e:
            logger.error(f"❌ Error resetting Web3 cache: {e}")
            self.stderr.write(self.style.ERROR(f"❌ Error resetting Web3 cache: {e}"))