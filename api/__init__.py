# api/__init__.py
default_app_config = 'api.apps.ApiConfig'

from drf_spectacular.extensions import OpenApiAuthenticationExtension
from .extensions import CustomAPIKeyAuthenticationExtension