from django.contrib import admin
from api.models import Event

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('event_idx', 'event_dt', 'contract_idx', 'contract_type', 'contract_release', 'network', 'from_addr', 'to_addr', 'tx_hash', 'gas_used', 'event_type', 'details', 'status')
    search_fields = ('event_idx', 'contract_type', 'event_type', 'tx_hash', 'network', 'from_addr', 'to_addr')
    list_filter = ('event_type', 'contract_type', 'contract_release', 'status', 'event_dt')

    # Optional: Customize the default ordering in the admin interface
    ordering = ('-event_dt',)  # Order by the most recent event by default

    # Make all fields readonly
    readonly_fields = [field.name for field in Event._meta.fields]

    # Disable adding new audit events
    def has_add_permission(self, request):
        return False

    # Disable deleting audit events (single and bulk deletes)
    def has_delete_permission(self, request, obj=None):
        return False

    # Disable bulk actions like "Delete selected"
    actions = None

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'View Audit Events'
        return super().changelist_view(request, extra_context=extra_context)
