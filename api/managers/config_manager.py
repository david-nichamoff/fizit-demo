import logging
import os
import json
from django.conf import settings

from api.utilities.logging import log_error, log_info, log_warning, log_debug

class ConfigManager():

    _instance = None
    _config_cache = None
    CONFIG_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'config', 'config.json')

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure only one instance of ConfigManager exists."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        """Initialize ConfigManager (lazy loading for configuration)."""
        if not hasattr(self, 'initialized'):
            self._config_cache = None  # Cache for loaded configurations
            self.initialized = True
            self.logger = logging.getLogger(__name__)

    def load_config(self):
        """
        Load configuration from `config.json`, caching the result after the first load.
        :raises FileNotFoundError: If the configuration file is missing.
        :raises JSONDecodeError: If the JSON format is invalid.
        """

        if self._config_cache is not None:
            log_debug(self.logger, "Configuration already loaded. Returning cached configuration.")
            return self._config_cache

        log_info(self.logger, f"Loading configuration from {self.CONFIG_FILE_PATH}")
        if not os.path.exists(self.CONFIG_FILE_PATH):
            log_error(self.logger, f"Configuration file not found: {self.CONFIG_FILE_PATH}")
            raise FileNotFoundError(f"Configuration file not found: {self.CONFIG_FILE_PATH}")

        self._config_cache = self._load_config_from_file()
        return self._config_cache

    def get_config_value(self, key, default=None):
        """
        Retrieve a specific configuration value.
        :param key: The configuration key to retrieve.
        :param default: The default value to return if the key is not found.
        :return: The configuration value or the default value.
        """
        if self._config_cache is None:
            self.load_config()

        value = self._config_cache.get(key, default)
        if value is default:
            log_warning(self.logger, f"Configuration key '{key}' not found. Returning default: {default}")
        return value

    def get_nested_config_value(self, parent_key, child_key, default=None):
        """
        Retrieve a value from a nested configuration where the parent key contains a list of dictionaries.
        :param parent_key: The parent key in the configuration.
        :param child_key: The key within the nested dictionaries.
        :param default: The default value to return if not found.
        :return: The nested configuration value or the default value.
        """
        nested_list = self.get_config_value(parent_key, [])
        if not isinstance(nested_list, list):
            log_error(self.logger, f"Expected a list for '{parent_key}', got: {type(nested_list)}")
            raise ValueError(f"Configuration '{parent_key}' must be a list.")

        value = next((item['value'] for item in nested_list if item.get('key') == child_key), default)
        if value is default:
            log_warning(self.logger, f"'{child_key}' not found in configuration '{parent_key}'. Returning default: {default}")
        return value

    def update_config_value(self, key, new_value):
        """
        Update a configuration value and persist changes to `config.json`.
        :param key: The key of the configuration to update.
        :param new_value: The new value for the configuration.
        :raises KeyError: If the key does not exist in the configuration.
        :raises Exception: For file write errors.
        """
        if self._config_cache is None:
            self.load_config()

        if key not in self._config_cache:
            error_message = f"Configuration key '{key}' not found. Cannot update." 
            log_error(self.logger, error_message)
            raise KeyError(error_message)

        self._config_cache[key] = new_value
        self._write_config_to_file()

    def _load_config_from_file(self):
        """
        Load the configuration file into a dictionary.
        :return: The configuration as a dictionary.
        :raises JSONDecodeError: If the JSON format is invalid.
        """
        try:
            with open(self.CONFIG_FILE_PATH, 'r') as config_file:
                config_list = json.load(config_file)

            # Convert list of dictionaries into a single dictionary
            config_dict = {item['key']: item['value'] for item in config_list}
            log_info(self.logger, f"Configuration loaded successfully from {self.CONFIG_FILE_PATH}")
            return config_dict

        except json.JSONDecodeError as e:
            log_error(self.logger, f"Error parsing configuration file: {e}")
            raise 
        except Exception as e:
            log_error(self.logger, f"Unexpected error loading configuration file: {e}")
            raise

    def _write_config_to_file(self):
        """
        Write the current configuration cache to `config.json`.
        :raises Exception: For file write errors.
        """
        try:
            with open(self.CONFIG_FILE_PATH, 'w') as config_file:
                config_list = [{"key": k, "value": v} for k, v in self._config_cache.items()]
                json.dump(config_list, config_file, indent=4)
            log_info(self.logger, f"Configuration successfully updated in {self.CONFIG_FILE_PATH}")

        except Exception as e:
            log_error(self.logger, f"Error writing to configuration file: {e}")
            raise