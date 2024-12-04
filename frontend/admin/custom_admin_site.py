from django.contrib.auth.models import User, Group
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path, reverse
from ...api.admin.event_admin import EventAdmin
from ...api.admin.contact_admin import ContactAdmin
from ...api.admin.contract_admin import ContractAdmin
from ...api.models import Event, Contact, Contract

from ...api.admin.avax_balances import avax_balances_view
from ...api.admin.fizit_balances import fizit_balances_view
from ...api.admin.erc20_balances import erc20_balances_view
from ...api.admin.view_contract import view_contract_view
from ...api.admin.list_contracts import list_contracts_view
from ...api.admin.add_contract import add_contract_view

import logging

logger = logging.getLogger(__name__)

class CustomAdminSite(AdminSite):
    site_header = "FIZIT Admin"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def has_permission(self, request):
        logger.info(f"Checking permissions for user: {request.user}")
        if request.user.is_active and request.user.is_staff:
            logger.info("Permission granted")
            return True
        logger.warning("Permission denied")
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('avax-balances/', self.admin_view(self.avax_balances_view), name='avax_balances'),
            path('fizit-balances/', self.admin_view(self.fizit_balances_view), name='fizit_balances'),
            path('erc20-balances/', self.admin_view(self.erc20_balances_view), name='erc20_balances'),
            path('view-contract/', self.admin_view(self.view_contract_view), name='view_contract'),  
            path('list-contracts/', self.admin_view(self.list_contracts_view), name='list_contracts'),  
            path('add-contract/', self.admin_view(self.add_contract_view), name='add_contract'),  
        ]
        return custom_urls + urls

    def avax_balances_view(self, request):
        logger.info("Accessing AVAX Balances view")
        context = self.each_context(request)
        return avax_balances_view(request, extra_context=context)

    def fizit_balances_view(self, request):
        logger.info("Accessing FIZIT Balances view")
        context = self.each_context(request)
        return fizit_balances_view(request, extra_context=context)

    def erc20_balances_view(self, request):
        logger.info("Accessing ERC20 Balances view")
        context = self.each_context(request)
        return erc20_balances_view(request, extra_context=context)

    def view_contract_view(self, request):
        logger.info("Accessing View Contract page")
        context = self.each_context(request)
        return view_contract_view(request, extra_context=context)

    def list_contracts_view(self, request):
        logger.info("Accessing List Contracts page")
        context = self.each_context(request)
        return list_contracts_view(request, extra_context=context)

    def add_contract_view(self, request):
        logger.info("Accessing Add Contract page")
        context = self.each_context(request)
        return add_contract_view(request, extra_context=context)

    def each_context(self, request):
        """
        Add custom links to the sidebar context.
        """
        context = super().each_context(request)
        # Custom links grouped by sections
        context['custom_links'] = [
            {
                'section': 'Balances',
                'links': [
                    {'name': 'AVAX Balances', 'url': reverse('custom_admin:avax_balances')},
                    {'name': 'FIZIT Balances', 'url': reverse('custom_admin:fizit_balances')},
                    {'name': 'ERC20 Balances', 'url': reverse('custom_admin:erc20_balances')},
                ],
            },
            {
                'section': 'Contracts',
                'links': [
                    {'name': 'List Contracts', 'url': reverse('custom_admin:list_contracts')},
                    {'name': 'Add Contract', 'url': reverse('custom_admin:add_contract')},
                ],
            },
        ]
        logger.info(f"Sidebar context custom_links: {context['custom_links']}")
        return context


    def index(self, request, extra_context=None):
        """
        Custom index view to display the FIZIT logo.
        """
        logger.info("CustomAdminSite index method called")
        context = {
            **self.each_context(request),
            'title': self.index_title,
            **(extra_context or {}),
        }
        return TemplateResponse(request, 'admin/custom_index.html', context)

# Create an instance of CustomAdminSite
custom_admin_site = CustomAdminSite(name='custom_admin')

# Register models with the custom admin site
try:
    custom_admin_site.register(Event, EventAdmin)
    custom_admin_site.register(Contact, ContactAdmin)
    custom_admin_site.register(Contract, ContractAdmin)
    from django.contrib.auth.admin import UserAdmin, GroupAdmin
    custom_admin_site.register(User, UserAdmin)
    custom_admin_site.register(Group, GroupAdmin)
except Exception as e:
    logger.error(f"Failed to register models: {e}")