import logging
from django.core.management.base import BaseCommand
from api.config import ConfigManager

class Command(BaseCommand):
    help = "Refresh the configuration cache from the JSON file."

    def handle(self, *args, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            config_manager = ConfigManager()
            config_manager.update_config()
            self.stdout.write(self.style.SUCCESS("✅ Configuration cache successfully updated."))
        except Exception as e:
            logger.error(f"❌ Error updating configuration cache: {e}")
            self.stderr.write(self.style.ERROR(f"❌ Error updating configuration cache: {e}"))