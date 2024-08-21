from django.contrib import admin
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.admin import APIKeyModelAdmin

from .models import EngageSrc, EngageDest
from .models import CustomAPIKey, DataDictionary 
from .models import ContractEvent, ContactRequest, Configuration
from .models import PartyCode, PartyType

# Unregister the default APIKey model if it is registered
if APIKey in admin.site._registry:
    admin.site.unregister(APIKey)

@admin.register(EngageSrc)
class EngageSrcAdmin(admin.ModelAdmin):
    list_display = ('src_id', 'api_key', 'src_code')
    search_fields = ('src_code',)

@admin.register(EngageDest)
class EngageDestAdmin(admin.ModelAdmin):
    list_display = ('dest_id', 'dest_code')
    search_fields = ('dest_code',)

@admin.register(CustomAPIKey)
class CustomAPIKeyModelAdmin(APIKeyModelAdmin):
    fields = ('name', 'parties')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            api_key, key = CustomAPIKey.objects.create_key(name=obj.name)
            obj.prefix = api_key.prefix
            obj.hashed_key = api_key.hashed_key
        super().save_model(request, obj, form, change)

@admin.register(DataDictionary)
class DataDictionaryAdmin(admin.ModelAdmin):
    list_display = ('type', 'field_code', 'display_name', 'language_code')
    search_fields = ('type', 'field_code', 'display_name', 'language_code')
    list_filter = ('type', 'language_code')

@admin.register(ContractEvent)
class ContractEventAdmin(admin.ModelAdmin):
    list_display = ('event_idx','contract_idx','contract_addr','event_type','details','event_dt')
    search_fields = ('event_idx','contract_idx','contract_addr','event_type')
    list_filter = ('event_idx','contract_idx','contract_addr','event_type')

@admin.register(ContactRequest)
class ContactRequestAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'message')
    search_fields = ('name', 'email', 'company')
    list_display = ('name', 'email', 'company')

@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ('key', 'config_type', 'value')
    search_fields = ('key', 'config_type')
    list_filter = ('config_type',)

@admin.register(PartyCode)
class PartyAdmin(admin.ModelAdmin):
    list_display = ('party_code', 'address')
    search_fields = ('party_code',)
    list_filter = ('party_code',)

@admin.register(PartyType)
class PartyTypeAdmin(admin.ModelAdmin):
    list_display = ('party_type',)
    search_fields = ('party_type',)
    list_filter = ('party_type',)