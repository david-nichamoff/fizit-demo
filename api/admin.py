from django.contrib import admin
from .models import EngageSrc, EngageDest

@admin.register(EngageSrc)
class EngageSrcAdmin(admin.ModelAdmin):
    list_display = ('src_id', 'api_key', 'src_code')
    search_fields = ('src_code',)

@admin.register(EngageDest)
class EngageDestAdmin(admin.ModelAdmin):
    list_display = ('dest_id', 'dest_code')
    search_fields = ('dest_code',)