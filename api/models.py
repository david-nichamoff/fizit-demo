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
    parties = models.CharField(max_length=255, blank=True, null=True, help_text="Comma-separated list of party codes this API key can access.")

    class Meta:
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

class DataDictionary(models.Model):
    type = models.CharField(max_length=50)
    field_code = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    language_code = models.CharField(max_length=10, default='en')  # Add language_code field

    def __str__(self):
        return f"{self.type} - {self.field_code} ({self.language_code}): {self.display_name}"

    class Meta:
        unique_together = ('type', 'field_code', 'language_code')
        verbose_name_plural = 'Data Dictionary'

class ContractEvent(models.Model):
    event_idx = models.AutoField(primary_key=True) 
    contract_idx = models.IntegerField()
    event_type = models.CharField(max_length=50)
    details = models.CharField(max_length=255)
    event_dt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Contract {self.contract_idx} updated at {self.event_dt}'

    class Meta:
        verbose_name = "Contract Event"
        verbose_name_plural = "Contract Events"

class ContactRequest(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    company = models.CharField(max_length=100, blank=True)
    message = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Contract Request"
        verbose_name_plural = "Contract Requests"