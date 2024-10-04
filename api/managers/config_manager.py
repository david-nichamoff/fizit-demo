import logging
import os
import json
from django.conf import settings

logger = logging.getLogger(__name__)

class ConfigManager:
    _instance = None
    _config_cache = None
    CONFIG_FILE_PATH = os.path.join(settings.BASE_DIR, 'api', 'managers', 'fixtures', 'config.json')

    def __new__(cls, *args, **kwargs):
        """Ensure that the class is a singleton."""
        if not cls._instance:
            cls._instance = super(ConfigManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        pass

    def load_config(self):
        """Load configuration from config.json, caching it after the first load."""
        if self._config_cache is not None:
            logger.info("Configuration cache found, returning cached config.")
            return self._config_cache

        # Initialize the config cache as an empty dictionary
        self._config_cache = {}

        # Load config.json into the cache
        if not os.path.exists(self.CONFIG_FILE_PATH):
            logger.error(f"Configuration file not found at {self.CONFIG_FILE_PATH}")
            raise FileNotFoundError(f"Configuration file not found at {self.CONFIG_FILE_PATH}")

        logger.info(f"Loading config from {self.CONFIG_FILE_PATH}")

        try:
            with open(self.CONFIG_FILE_PATH, 'r') as config_file:
                config_list = json.load(config_file)
            
            # Convert the list of dictionaries to a single dictionary
            for config in config_list:
                key = config['key']
                value = config['value']
                self._config_cache[key] = value

        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config.json: {e}")
            raise
        except Exception as e:
            logger.error(f"An error occurred while loading config.json: {e}")
            raise

        logger.info("Configuration loading complete.")
        return self._config_cache

    def get_config_value(self, key, default=None):
        """Get a specific configuration value from the loaded configuration."""
        if self._config_cache is None:
            logger.info(f"Configuration cache is empty, reloading config for key: {key}")
            self.load_config()

        # Return the value associated with the key, or default if not found
        return self._config_cache.get(key, default)

    def update_config_value(self, key, new_value):
        """Update a specific configuration value and write it back to the JSON file."""
        if self._config_cache is None:
            self.load_config()

        # Update the value in the cache
        if key in self._config_cache:
            self._config_cache[key] = new_value
            logger.info(f"Updating config: {key} = {new_value}")
        else:
            logger.error(f"Config key '{key}' not found.")
            raise KeyError(f"Config key '{key}' not found.")

        try:
            with open(self.CONFIG_FILE_PATH, 'w') as config_file:
                json_data = [{"key": k, "value": v} for k, v in self._config_cache.items()]
                json.dump(json_data, config_file, indent=4)
            logger.info(f"Configuration successfully updated in {self.CONFIG_FILE_PATH}.")
        except Exception as e:
            logger.error(f"An error occurred while writing to the config file: {e}")
            raise