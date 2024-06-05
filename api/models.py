from django.db import models
from rest_framework_api_key.models import AbstractAPIKey

class EngageSrc(models.Model):
    src_idx = models.AutoField(primary_key=True)
    src_id = models.IntegerField(unique=True)
    api_key = models.CharField(max_length=100)
    src_code = models.CharField(unique=True, max_length=25)

    def __str__(self):
        return self.src_code

    class Meta:
        verbose_name = "Engage Source"
        verbose_name_plural = "Engage Sources"

class EngageDest(models.Model):
    dest_idx = models.AutoField(primary_key=True)
    dest_id = models.IntegerField(unique=True)
    dest_code = models.CharField(unique=True, max_length=25)

    def __str__(self):
        return self.dest_code

    class Meta:
        verbose_name = "Engage Destination"
        verbose_name_plural = "Engage Destinations"

class CustomAPIKey(AbstractAPIKey):
    contract_ids = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated list of contract IDs this API key can access.")
    account_ids = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated list of account IDs this API key can access.")
    restricted_functions = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated list of restricted functions.")

    @classmethod
    def get_from_key(cls, key: str) -> 'CustomAPIKey':
        prefix, _, _ = key.partition(".")
        hashed_key = KeyGenerator().hash(key)
        return cls.objects.get(prefix=prefix, hashed_key=hashed_key)