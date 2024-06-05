from django.contrib import admin
from rest_framework_api_key.models import APIKey
from rest_framework_api_key.admin import APIKeyModelAdmin
from .models import EngageSrc, EngageDest, CustomAPIKey

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
    fields = ('name', 'contract_ids', 'account_ids', 'restricted_functions')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            api_key, key = CustomAPIKey.objects.create_key(name=obj.name)
            obj.prefix = api_key.prefix
            obj.hashed_key = api_key.hashed_key
        super().save_model(request, obj, form, change)