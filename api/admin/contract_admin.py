from django.contrib import admin
from ..models import Contract

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_addr', 'created_dt', 'expiry_dt')
    search_fields = ('contract_addr', 'created_dt', 'expiry_dt')
    list_display = ('contract_addr', 'created_dt', 'expiry_dt')