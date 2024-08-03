import os

from api.models import Configuration

_env_config = None

def load_config():
    global _env_config
    python_path = os.environ['PYTHONPATH']

    if _env_config is None:
        _env_config = {}

        configs = Configuration.objects.all()
        for config in configs:
            if config.config_type == "string":
                _env_config[config.key] = config.value
            else:
                _env_config[config.key] = int(config.value)

    return _env_config