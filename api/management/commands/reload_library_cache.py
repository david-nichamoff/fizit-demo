import logging
from django.core.management.base import BaseCommand
from api.library import LibraryManager

class Command(BaseCommand):
    help = "Reload the library cache from the JSON file."

    def handle(self, *args, **kwargs):
        logger = logging.getLogger(__name__)
        try:
            library_manager = LibraryManager()
            library_manager.reset_library_cache()
            self.stdout.write(self.style.SUCCESS("✅ Library cache successfully updated."))
        except Exception as e:
            logger.error(f"❌ Error updating library cache: {e}")
            self.stderr.write(self.style.ERROR(f"❌ Error updating library cache: {e}"))