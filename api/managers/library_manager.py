import os
import json
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class LibraryManager:
    """
    A manager to handle the library of standard transaction logics.
    Loads a library.json file and provides methods to interact with the stored data.
    """
    _instance = None
    _library_cache = None
    LIBRARY_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'managers', 'fixtures', 'library.json')

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(LibraryManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self._library_cache = {}  # Ensure _library_cache is initialized
        self.load_library()

    def load_library(self):
        """Load library.json into _library_cache."""
        if not os.path.exists(self.LIBRARY_FILE_PATH):
            logger.error(f"Library file not found at {self.LIBRARY_FILE_PATH}")
            raise FileNotFoundError(f"Library file not found at {self.LIBRARY_FILE_PATH}")

        try:
            with open(self.LIBRARY_FILE_PATH, 'r') as library_file:
                library_data = json.load(library_file)

            # Populate the cache with contract_type and its logics
            for item in library_data:
                contract_type = item['contract_type']
                logics = item.get('logics', [])
                self._library_cache[contract_type] = logics

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing library.json: {e}")
            self._library_cache = {}  # Reset the cache on error
        except Exception as e:
            logger.error(f"An unexpected error occurred while loading library.json: {e}")
            self._library_cache = {}


    def get_logics_by_contract_type(self, contract_type):
        """
        Retrieve all logics for a given contract type.
        :param contract_type: The contract type to filter by.
        :return: A list of logics with their descriptions.
        """
        if self._library_cache is None:
            self.load_library()

        for entry in self._library_cache:
            if entry.get("contract_type") == contract_type:
                return entry.get("logics", [])

        logger.warning(f"No logics found for contract type: {contract_type}")
        return []

    def add_logic(self, contract_type, transact_logic, description):
        """
        Add a new logic to the library.
        :param contract_type: The contract type to add the logic to.
        :param transact_logic: The transaction logic JSON structure.
        :param description: The description of the logic.
        """
        if self._library_cache is None:
            self.load_library()

        # Find or create the entry for the given contract type
        for entry in self._library_cache:
            if entry.get("contract_type") == contract_type:
                entry["logics"].append({
                    "transact_logic": transact_logic,
                    "description": description
                })
                break
        else:
            # If no entry exists, create a new one
            self._library_cache.append({
                "contract_type": contract_type,
                "logics": [
                    {
                        "transact_logic": transact_logic,
                        "description": description
                    }
                ]
            })

        # Save the updated library to the file
        self._save_library()

    def get_templates_by_contract_type(self, contract_type):
        """Retrieve templates for a given contract_type."""
        if self._library_cache is None:
            self.load_library()
        return self._library_cache.get(contract_type, [])

    def _save_library(self):
        """Write the current library cache back to the library.json file."""
        try:
            with open(self.LIBRARY_FILE_PATH, 'w') as library_file:
                json.dump(self._library_cache, library_file, indent=4)
        except Exception as e:
            logger.error(f"An error occurred while writing to the library file: {e}")
            raise