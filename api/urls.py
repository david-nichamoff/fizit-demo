from django.urls import path

from .views.contract_views import ContractViewSet
from .views.party_views import PartyViewSet
from .views.settlement_views import SettlementViewSet
from .views.transaction_views import TransactionViewSet
from .views.ticket_views import TicketViewSet
from .views.invoice_views import InvoiceViewSet
from .views.artifact_views import ArtifactViewSet
from .views.account_views import AccountViewSet
from .views.deposit_views import DepositViewSet
from .views.recipient_views import RecipientViewSet
from .views.event_views import ContractEventViewSet
from .views.address_views import ContractAddressViewSet

from .views.csrf_token_views import get_csrf_token

urlpatterns = [
    path('contracts/', ContractViewSet.as_view({'get':'list','post':'add'}), name='contract-list'),
    path('contracts/<int:contract_idx>/', ContractViewSet.as_view({'get':'get','patch':'patch','delete':'delete'}), name='contract-detail'),
    path('contracts/<int:contract_idx>/parties/', PartyViewSet.as_view({'get':'list_contract','post':'add','delete':'delete_contract'}), name='contract-parties'),
    path('contracts/<int:contract_idx>/parties/<int:party_idx>', PartyViewSet.as_view({'delete':'delete'}), name='contract-party'),
    path('contracts/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get':'list_contract','post':'add','delete':'delete_contract'}), name='contract-transactions'),
    path('contracts/<int:contract_idx>/tickets/', TicketViewSet.as_view({'get':'list_contract','post':'process'}), name='contract-tickets'),
    path('contracts/<int:contract_idx>/invoices/', InvoiceViewSet.as_view({'get':'list_contract'}), name='contract-invoices'),
    path('contracts/<int:contract_idx>/settlements/', SettlementViewSet.as_view({'get':'list_contract','post':'add','delete':'delete_contract'}), name='contract-settlements'),
    path('contracts/<int:contract_idx>/artifacts/', ArtifactViewSet.as_view({'get':'list_contract','post':'add','delete':'delete_contract'}), name='contract-artifacts'),
    path('accounts/', AccountViewSet.as_view({'get':'list'}), name='account-list'),
    path('accounts/<str:account_id>/pay-advance/', AccountViewSet.as_view({'post':'pay_advance'}), name='pay-advance'),
    path('accounts/<str:account_id>/pay-residual/', AccountViewSet.as_view({'post':'pay_residual'}), name='pay-residual'),
    path('accounts/<str:account_id>/post-settlement/', AccountViewSet.as_view({'post':'post_settlement'}), name='post-settlement'),
    path('accounts/<str:account_id>/deposits/', DepositViewSet.as_view({'get':'list'}), name='deposit-list'),
    path('recipients/', RecipientViewSet.as_view({'get':'list'}), name='recipient-list'),
    path('contract-events/', ContractEventViewSet.as_view({'get': 'list'}), name='contract-event-list'),  
    path('current-contract-addr/', ContractAddressViewSet.as_view({'get':'get'}), name='current-contract-addr'),
    path('get-csrf-token/', get_csrf_token, name='get_csrf_token'),
]