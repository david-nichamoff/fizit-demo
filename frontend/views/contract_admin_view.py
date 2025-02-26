from django.contrib import admin
from api.models import SmartContract

@admin.register(SmartContract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_type', 'contract_addr', 'created_dt', 'expiry_dt')
    search_fields = ('contract_type', 'contract_addr', 'created_dt', 'expiry_dt')
    list_display = ('contract_type', 'contract_addr', 'created_dt', 'expiry_dt')