from api.managers.app_context import AppContext
from api.managers.cache_manager import CacheManager
from api.managers.config_manager import ConfigManager
from api.managers.secrets_manager import SecretsManager
from api.managers.domain_manager import DomainManager
from api.managers.web3_manager import Web3Manager
from api.managers.api_manager import APIManager
from api.managers.adapter_manager import AdapterManager
from api.managers.library_manager import LibraryManager
from api.managers.serializer_manager import SerializerManager
from api.managers.form_manager import FormManager

def build_app_context():
    # Step 1: Create context-independent managers
    cache = CacheManager()
    config = ConfigManager()
    secrets = SecretsManager()
    domain = DomainManager()

    # Step 2: Build context
    context = AppContext(
        cache_manager=cache,
        config_manager=config,
        secrets_manager=secrets,
        domain_manager=domain,
    )

    # Step 3: Add higher-level managers
    context.web3_manager = Web3Manager(context)
    context.api_manager = APIManager(context)
    context.adapter_manager = AdapterManager(context)
    context.library_manager = LibraryManager()
    context.serializer_manager = SerializerManager()
    context.form_manager  = FormManager()

    return context