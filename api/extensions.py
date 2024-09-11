from drf_spectacular.extensions import OpenApiAuthenticationExtension

class CustomAPIKeyAuthenticationExtension(OpenApiAuthenticationExtension):
    target_class = 'api.authentication.AWSSecretsAPIKeyAuthentication'  # full import path OR class ref
    name = 'FIZIT Authorization'
    match_subclasses = True

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Use "Api-Key {api_key}" format.'
        }