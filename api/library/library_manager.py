import os
import json
import logging

from django.conf import settings

from api.utilities.logging import log_error, log_info, log_warning

class LibraryManager():
    """
    A manager to handle the library of standard transaction logics.
    Loads a library.json file and provides methods to interact with the stored data.
    """
    _instance = None
    _library_cache = None
    LIBRARY_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'library', 'library.json')

    def __new__(cls, *args, **kwargs):
        """Ensure the class is a singleton."""
        if not cls._instance:
            cls._instance = super(LibraryManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.logger = logging.getLogger(__name__)

    def load_library(self):
        """
        Load library.json into _library_cache, caching it for future use.
        """
        if self._library_cache is not None:
            return self._library_cache

        # Initialize the library cache
        self._library_cache = {}

        if not os.path.exists(self.LIBRARY_FILE_PATH):
            log_error(self.logger, f"Library file not found at {self.LIBRARY_FILE_PATH}")
            raise FileNotFoundError(f"Library file not found at {self.LIBRARY_FILE_PATH}")

        try:
            with open(self.LIBRARY_FILE_PATH, 'r') as library_file:
                library_data = json.load(library_file)

            # Convert the loaded data into a dictionary for easier access
            for item in library_data:
                contract_type = item['contract_type']
                self._library_cache[contract_type] = item.get('logics', [])

            log_info(self.logger, "Library successfully loaded and cached.")
        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing library.json: {e}")
            raise
        except Exception as e:
            log_error(self.logger, f"Unexpected error while loading library.json: {e}")
            raise

        return self._library_cache

    def get_logics_by_contract_type(self, contract_type):
        """
        Retrieve all logics for a given contract type.
        :param contract_type: The contract type to filter by.
        :return: A list of logics or an empty list if none are found.
        """
        if self._library_cache is None:
            self.load_library()

        logics = self._library_cache.get(contract_type, [])
        if not logics:
            log_warning(self.logger, f"No logics found for contract type '{contract_type}'.")
        return logics

    def add_logic(self, contract_type, transact_logic, description):
        """
        Add a new logic to the library for a specific contract type.
        :param contract_type: The contract type to add the logic to.
        :param transact_logic: The transaction logic JSON structure.
        :param description: The description of the logic.
        """
        if self._library_cache is None:
            self.load_library()

        if contract_type not in self._library_cache:
            self._library_cache[contract_type] = []

        self._library_cache[contract_type].append({
            "transact_logic": transact_logic,
            "description": description
        })

        log_info(self.logger, f"Added new logic to contract type '{contract_type}'.")
        self._save_library()

    def get_templates_by_contract_type(self, contract_type):
        """
        Retrieve templates (logics) for a given contract type.
        :param contract_type: The contract type to filter by.
        :return: A list of templates or an empty list if none are found.
        """
        if self._library_cache is None:
            self.load_library()

        templates = self._library_cache.get(contract_type, [])
        if not templates:
            log_warning(self.logger, f"No templates found for contract type '{contract_type}'.")
        return templates

    def update_logic(self, contract_type, logic_index, new_logic, new_description):
        """
        Update an existing logic for a contract type.
        :param contract_type: The contract type to update.
        :param logic_index: The index of the logic to update.
        :param new_logic: The new transaction logic JSON structure.
        :param new_description: The new description for the logic.
        """
        if self._library_cache is None:
            self.load_library()

        if contract_type not in self._library_cache:
            log_error(self.logger, f"Contract type '{contract_type}' does not exist.")
            raise KeyError(f"Contract type '{contract_type}' does not exist.")

        logics = self._library_cache[contract_type]
        if logic_index < 0 or logic_index >= len(logics):
            log_error(self.logger, f"Logic index '{logic_index}' out of range for contract type '{contract_type}'.")
            raise IndexError(f"Logic index '{logic_index}' out of range.")

        logics[logic_index] = {
            "transact_logic": new_logic,
            "description": new_description
        }
        log_info(self.logger, f"Updated logic at index {logic_index} for contract type '{contract_type}'.")
        self._save_library()

    def _save_library(self):
        """
        Save the current library cache to library.json.
        """
        try:
            with open(self.LIBRARY_FILE_PATH, 'w') as library_file:
                library_data = [{"contract_type": k, "logics": v} for k, v in self._library_cache.items()]
                json.dump(library_data, library_file, indent=4)
                log_info(self.logger, "Library file successfully saved.")
        except Exception as e:
            log_error(self.logger, f"Error writing to library file: {e}")
            raise