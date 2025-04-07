import os
import json
import logging

from django.conf import settings

from api.managers.cache_manager import CacheManager
from api.utilities.logging import log_error, log_info, log_warning

class LibraryManager():

    LIBRARY_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'managers', 'fixtures', 'library.json')

    def __init__(self):
        self.cache_manager = CacheManager()
        self.cache_key = self.cache_manager.get_library_cache_key()
        self.logger = logging.getLogger(__name__)

    def load_library(self):
        library_cache = self.cache_manager.get(self.cache_key)

        if library_cache:
            return library_cache

        return self._reload_library_from_file()

    def _reload_library_from_file(self):

        if not os.path.exists(self.LIBRARY_FILE_PATH):
            log_error(self.logger, f"Library file not found at {self.LIBRARY_FILE_PATH}")
            raise FileNotFoundError(f"Library file not found at {self.LIBRARY_FILE_PATH}")

        try:
            with open(self.LIBRARY_FILE_PATH, 'r') as library_file:
                library_data = json.load(library_file)

            # Convert to dictionary structure {contract_type: [logics]}
            library_cache = {item["contract_type"]: item.get("logics", []) for item in library_data}
            self.cache_manager.set(self.cache_key, library_cache, timeout=None)

            return library_cache

        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing library.json: {e}")
            raise
        except Exception as e:
            log_error(self.logger, f"Unexpected error while loading library.json: {e}")
            raise

    def reset_library_cache(self):
        self.cache_manager.delete(self.cache_key)
        return self._reload_library_from_file()

    def add_template(self, contract_type, transact_logic, description):
        library_cache = self.load_library()

        library_cache[contract_type].append({
            "transact_logic": transact_logic,
            "description": description
        })

        # Update Redis cache
        self.cache_manager.set(self.cache_key, library_cache, timeout=None)
        self._save_library(library_cache)

    def get_templates_by_contract_type(self, contract_type):
        library_cache = self.load_library()
        templates = library_cache.get(contract_type, [])

        if not templates:
            log_warning(self.logger, f"No templates found for contract type '{contract_type}'.")

        return templates

    def _save_library(self, library_cache):

        try:
            with open(self.LIBRARY_FILE_PATH, 'w') as library_file:
                library_data = [{"contract_type": k, "logics": v} for k, v in library_cache.items()]
                json.dump(library_data, library_file, indent=4)
                log_info(self.logger, "Library file successfully saved.")

        except Exception as e:
            log_error(self.logger, f"Error writing to library file: {e}")
            raise