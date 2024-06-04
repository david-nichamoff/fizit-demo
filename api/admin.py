from django.contrib import admin
from rest_framework_api_key.models import APIKey
from .models import EngageSrc, EngageDest

@admin.register(EngageSrc)
class EngageSrcAdmin(admin.ModelAdmin):
    list_display = ('src_id', 'api_key', 'src_code')
    search_fields = ('src_code',)

@admin.register(EngageDest)
class EngageDestAdmin(admin.ModelAdmin):
    list_display = ('dest_id', 'dest_code')
    search_fields = ('dest_code',)

admin.site.register(APIKey)