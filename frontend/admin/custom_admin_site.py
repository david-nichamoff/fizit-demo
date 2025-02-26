import logging

from django.contrib.auth.models import User, Group
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path, reverse

from api.models import Event, SmartContract

from frontend.views import erc20_balances_view, avax_balances_view, fizit_balances_view, mercury_balances_view
from frontend.views import view_contract_view, list_contracts_view, add_contract_view
from frontend.views import add_transaction_view, add_advance_view, add_residual_view
from frontend.views import add_distribution_view, post_deposit_view, find_deposits_view
from frontend.views import EventAdmin, ContractAdmin

from api.utilities.logging import log_info, log_warning, log_error

logger = logging.getLogger(__name__)

class CustomAdminSite(AdminSite):
    site_header = "FIZIT Admin"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def has_permission(self, request):
        if request.user.is_active and request.user.is_staff:
            return True
        log_warning(logger, "Permission denied")
        return False

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('avax-balances/', self.admin_view(self.avax_balances_view), name='avax_balances'),
            path('fizit-balances/', self.admin_view(self.fizit_balances_view), name='fizit_balances'),
            path('erc20-balances/', self.admin_view(self.erc20_balances_view), name='erc20_balances'),
            path('mercury-balances/', self.admin_view(self.mercury_balances_view), name='mercury_balances'),
            path('view-contract/', self.admin_view(self.view_contract_view), name='view_contract'),  
            path('list-contracts/', self.admin_view(self.list_contracts_view), name='list_contracts'),  
            path('add-contract/', self.admin_view(self.add_contract_view), name='add_contract'),  
            path('add-transaction/', self.admin_view(self.add_transaction_view), name='add_transaction'),  
            path('add-advance/', self.admin_view(self.add_advance_view), name='add_advance'),  
            path('find-deposits/', self.admin_view(self.find_deposits_view), name='find_deposits'),  
            path('post-deposit/', self.admin_view(self.post_deposit_view), name='post_deposit'),  
            path('add-residual/', self.admin_view(self.add_residual_view), name='add_residual'),  
            path('add-distribution/', self.admin_view(self.add_distribution_view), name='add_distribution'),  
        ]
        return custom_urls + urls

    def avax_balances_view(self, request):
        context = self.each_context(request)
        return avax_balances_view(request, extra_context=context)

    def fizit_balances_view(self, request):
        context = self.each_context(request)
        return fizit_balances_view(request, extra_context=context)

    def erc20_balances_view(self, request):
        context = self.each_context(request)
        return erc20_balances_view(request, extra_context=context)

    def mercury_balances_view(self, request):
        context = self.each_context(request)
        return mercury_balances_view(request, extra_context=context)

    def view_contract_view(self, request):
        context = self.each_context(request)
        return view_contract_view(request, extra_context=context)

    def list_contracts_view(self, request):
        context = self.each_context(request)
        return list_contracts_view(request, extra_context=context)

    def add_contract_view(self, request):
        context = self.each_context(request)
        return add_contract_view(request, extra_context=context)

    def add_transaction_view(self, request):
        context = self.each_context(request)
        return add_transaction_view(request, extra_context=context)

    def add_advance_view(self, request):
        context = self.each_context(request)
        return add_advance_view(request, extra_context=context)

    def add_residual_view(self, request):
        context = self.each_context(request)
        return add_residual_view(request, extra_context=context)

    def add_distribution_view(self, request):
        context = self.each_context(request)
        return add_distribution_view(request, extra_context=context)

    def find_deposits_view(self, request):
        context = self.each_context(request)
        return find_deposits_view(request, extra_context=context)

    def post_deposit_view(self, request):
        context = self.each_context(request)
        return post_deposit_view(request, extra_context=context)

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
                    {'name': 'AVAX', 'url': reverse('custom_admin:avax_balances')},
                    {'name': 'FIZIT', 'url': reverse('custom_admin:fizit_balances')},
                    {'name': 'ERC20', 'url': reverse('custom_admin:erc20_balances')},
                    {'name': 'Mercury', 'url': reverse('custom_admin:mercury_balances')},
                ],
            },
            {
                'section': 'Contracts',
                'links': [
                    {'name': 'List Contracts', 'url': reverse('custom_admin:list_contracts')},
                    {'name': 'Add Transactions', 'url': reverse('custom_admin:add_transaction')},
                    {'name': 'Pay Advances', 'url': reverse('custom_admin:add_advance')},
                    {'name': 'Find Deposits', 'url': reverse('custom_admin:find_deposits')},
                    {'name': 'Post Deposit', 'url': reverse('custom_admin:post_deposit')},
                    {'name': 'Pay Residuals', 'url': reverse('custom_admin:add_residual')},
                    {'name': 'Pay Distributions', 'url': reverse('custom_admin:add_distribution')},
                ],
            }
        ]

        return context

    def index(self, request, extra_context=None):
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
    custom_admin_site.register(SmartContract, ContractAdmin)
    from django.contrib.auth.admin import UserAdmin, GroupAdmin
    custom_admin_site.register(User, UserAdmin)
    custom_admin_site.register(Group, GroupAdmin)
except Exception as e:
    log_error(logger, f"Failed to register models: {e}")