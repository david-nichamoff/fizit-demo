import os
import json
import logging

from django.conf import settings
from django.core.cache import cache

from api.cache import CacheManager
from api.utilities.logging import log_error, log_info, log_warning

class LibraryManager():
    """
    A manager to handle the library of standard transaction logics.
    Loads a library.json file and provides methods to interact with the stored data.
    """
    _instance = None
    LIBRARY_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'library', 'library.json')

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(LibraryManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.cache_manager = CacheManager()
            self.logger = logging.getLogger(__name__)

            self.cache_key = self.cache_manager.get_library_cache_key()

    def load_library(self):
        """
        Load library.json into _library_cache, caching it for future use.
        """
        library_cache = cache.get(self.cache_key)

        if library_cache:
            log_info(self.logger, "Loaded library from cache")
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

            cache.set(self.cache_key, library_cache, timeout=None)
            log_info(self.logger, "Library reloaded from file and cached in Redis.")

            return library_cache

        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing library.json: {e}")
            raise
        except Exception as e:
            log_error(self.logger, f"Unexpected error while loading library.json: {e}")
            raise

    def reset_library_cache(self):
        cache.delete(self.cache_key)
        log_info(self.logger, "Library cache cleared.")
        return self._reload_library_from_file()

    def get_logics_by_contract_type(self, contract_type):
        """
        Retrieve all logics for a given contract type.
        :param contract_type: The contract type to filter by.
        :return: A list of logics or an empty list if none are found.
        """
        library_cache = self.load_library()
        logics = library_cache.get(contract_type, [])

        if not logics:
            log_info(self.logger, f"No logics found for contract type '{contract_type}'.")
        return logics

    def add_logic(self, contract_type, transact_logic, description):
        """
        Add a new logic to the library for a specific contract type.
        :param contract_type: The contract type to add the logic to.
        :param transact_logic: The transaction logic JSON structure.
        :param description: The description of the logic.
        """
        library_cache = self.load_library()

        library_cache[contract_type].append({
            "transact_logic": transact_logic,
            "description": description
        })

        # Update Redis cache
        cache.set(self.cache_key, library_cache, timeout=None)
        log_info(self.logger, f"Added new logic to contract type '{contract_type}'.")
        self._save_library(library_cache)

    def get_templates_by_contract_type(self, contract_type):
        """
        Retrieve templates (logics) for a given contract type.
        :param contract_type: The contract type to filter by.
        :return: A list of templates or an empty list if none are found.
        """
        library_cache = self.load_library()
        templates = library_cache.get(contract_type, [])

        if not templates:
            log_info(self.logger, f"No templates found for contract type '{contract_type}'.")
        return templates

    def _save_library(self):

        try:
            with open(self.LIBRARY_FILE_PATH, 'w') as library_file:
                library_data = [{"contract_type": k, "logics": v} for k, v in self._library_cache.items()]
                json.dump(library_data, library_file, indent=4)
                log_info(self.logger, "Library file successfully saved.")
        except Exception as e:
            log_error(self.logger, f"Error writing to library file: {e}")
            raise