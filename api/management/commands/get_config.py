import logging
from django.core.management.base import BaseCommand
from api.managers.config_manager import ConfigManager

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check configuration by loading and displaying config values'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Loading configurations from ConfigManager...'))

        # Initialize ConfigManager
        config_manager = ConfigManager()

        # Load the entire config, including additional files
        config_cache = config_manager.load_config()
        self.stdout.write(self.style.SUCCESS('Complete configuration cache:'))
        
        # Pretty print the config cache
        for key, value in config_cache.items():
            self.stdout.write(f'{key}: {value}')

        self.stdout.write(self.style.SUCCESS('Configuration check completed.'))