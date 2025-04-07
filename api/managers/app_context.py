class AppContext:
    def __init__(
        self,
        config_manager,
        domain_manager,
        cache_manager,
        secrets_manager,
    ):
        self.config_manager = config_manager
        self.domain_manager = domain_manager
        self.cache_manager = cache_manager
        self.secrets_manager = secrets_manager