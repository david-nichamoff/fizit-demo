from django.urls import path
from .views import *

urlpatterns = [
    path('contracts/', ContractViewSet.as_view({'post':'create'}), name='contract-list'),
    path('contracts/<int:contract_idx>/', ContractViewSet.as_view({'get':'retrieve', 'patch':'update', 'delete':'destroy'}), name='contract-detail'),
    path('contracts/<int:contract_idx>/parties/', PartyViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-parties'),
    path('contracts/<int:contract_idx>/parties/<int:party_idx>/', PartyViewSet.as_view({'delete':'delete'}), name='contract-party'),
    path('contracts/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-transactions'),
    path('contracts/<int:contract_idx>/settlements/', SettlementViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-settlements'),
    path('contracts/<int:contract_idx>/artifacts/', ArtifactViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-artifacts'),
    path('contracts/<int:contract_idx>/advances/', AdvanceViewSet.as_view({'get':'list', 'post':'create'}), name='advance'),
    path('contracts/<int:contract_idx>/residuals/', ResidualViewSet.as_view({'get':'list', 'post':'create'}), name='residual'),
    path('contracts/<int:contract_idx>/deposits/', DepositViewSet.as_view({'get':'list', 'post':'create'}), name='deposit'),
    path('contracts/count/', ContractViewSet.as_view({'get': 'count'}), name='contract-count'),
    path('accounts/', AccountViewSet.as_view({'get':'list'}), name='account-list'),
    path('recipients/', RecipientViewSet.as_view({'get':'list'}), name='recipient-list'),
    path('events/', EventViewSet.as_view({'get': 'list'}), name='event-list'),  
    path('contacts/', ContactViewSet.as_view({'get':'list', 'post':'create'}), name='contact-list'),
    path('contacts/<int:contact_idx>/', ContactViewSet.as_view({'delete':'delete'}), name='contact-detail'),
    path('get-csrf-token/', get_csrf_token, name='get_csrf_token'),
]