from django.contrib import admin
from .models import Event, Contact, Contract

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_idx', 'contract_idx', 'network', 'from_addr', 'to_addr', 'tx_hash', 'gas_used', 'event_type', 'details', 'status')
    search_fields = ('event_idx', 'contract_idx', 'event_type', 'tx_hash', 'network', 'from_addr', 'to_addr')
    list_filter = ('event_type', 'status', 'network', 'event_dt')

    # Optional: Customize the default ordering in the admin interface
    ordering = ('-event_dt',)  # Order by the most recent event by default

    # Optional: Customize the display of readonly fields
    readonly_fields = ('event_dt',)  # Mark auto-generated date fields as readonly

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company', 'message')
    search_fields = ('name', 'email', 'company')
    list_display = ('name', 'email', 'company')

@admin.register(Contract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_addr', 'created_dt', 'expiry_dt')
    search_fields = ('contract_addr', 'created_dt', 'expiry_dt')
    list_display = ('contract_addr', 'created_dt', 'expiry_dt')