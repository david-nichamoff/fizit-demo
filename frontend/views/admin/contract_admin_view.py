from django.contrib import admin
from api.models import SmartContract

@admin.register(SmartContract)
class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_type', 'contract_release', 'contract_addr', 'created_dt', 'expiry_dt')
    search_fields = ('contract_type', 'contract_release', 'contract_addr')
    list_filter = ('contract_type', 'contract_release', 'created_dt', 'expiry_dt')

    # Optional: Customize the default ordering in the admin interface
    ordering = ('-created_dt',)  # Order by the most recent event by default

    # Make all fields readonly
    readonly_fields = [field.name for field in SmartContract._meta.fields]

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
        extra_context['title'] = 'View Smart Contract History'
        return super().changelist_view(request, extra_context=extra_context)
