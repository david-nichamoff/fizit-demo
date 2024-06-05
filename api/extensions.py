from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CustomAPIKeyAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'api.authentication.CustomAPIKeyAuthentication'  # full import path OR class ref
    name = 'CustomAPIKeyAuth'
    match_subclasses = True

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Custom API key authentication. Use "Api-Key {api_key}" format.'
        }