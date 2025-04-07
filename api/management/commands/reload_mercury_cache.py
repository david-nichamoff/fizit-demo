import logging

from django.core.management.base import BaseCommand

from api.adapters.bank import MercuryAdapter

class Command(BaseCommand):
    help = "Reload the secrets cache from AWS Secrets Manager."

    def handle(self, *args, **kwargs):
        logger = logging.getLogger(__name__)

        try:
            mercury_adapter = MercuryAdapter()
            mercury_adapter.reset_mercury_cache()
            self.stdout.write(self.style.SUCCESS("✅ Mercury cache successfully updated."))
        except Exception as e:
            logger.error(f"❌ Error updating Mercury cache: {e}")
            self.stderr.write(self.style.ERROR(f"❌ Error updating Mercury cache: {e}"))