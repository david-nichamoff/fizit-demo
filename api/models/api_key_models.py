from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

class CustomAPIKey(AbstractAPIKey):
    parties = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated list of party codes this API key can access.")

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"