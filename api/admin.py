from django.contrib import admin
from .models import Event, Contact, Contract

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_idx','contract_idx','contract_addr','event_type','details','event_dt')
    search_fields = ('event_idx','contract_idx','contract_addr','event_type')
    list_filter = ('event_idx','contract_idx','contract_addr','event_type')

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