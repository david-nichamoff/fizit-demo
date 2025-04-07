import logging

from django.core.management.base import BaseCommand

from api.managers.secrets_manager import SecretsManager

class Command(BaseCommand):
    help = "Reload the secrets cache from AWS Secrets Manager."

    def handle(self, *args, **kwargs):
        logger = logging.getLogger(__name__)
        
        try:
            secrets_manager = SecretsManager()
            secrets_manager.reset_secret_cache()
            self.stdout.write(self.style.SUCCESS("✅ Secrets cache successfully updated."))
        except Exception as e:
            logger.error(f"❌ Error updating secrets cache: {e}")
            self.stderr.write(self.style.ERROR(f"❌ Error updating secrets cache: {e}"))