from django.urls import path

from .views import ContractViewSet, PartyViewSet, SettlementViewSet
from .views import TransactionViewSet, ArtifactViewSet, AccountViewSet
from .views import RecipientViewSet, EventViewSet, AddressViewSet
from .views import ResidualViewSet, AdvanceViewSet, DepositViewSet
from .views import ContactViewSet, LibraryViewSet, get_csrf_token

urlpatterns = [
    path('contracts/', ContractViewSet.as_view({'get':'list','post':'add'}), name='contract-list'),
    path('contracts/<int:contract_idx>/', ContractViewSet.as_view({'get':'get','patch':'patch','delete':'delete'}), name='contract-detail'),
    path('contracts/<int:contract_idx>/parties/', PartyViewSet.as_view({'get':'list','post':'add','delete':'delete_contract'}), name='contract-parties'),
    path('contracts/<int:contract_idx>/parties/<int:party_idx>/', PartyViewSet.as_view({'delete':'delete'}), name='contract-party'),
    path('contracts/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get':'list','post':'add','delete':'delete_contract'}), name='contract-transactions'),
    path('contracts/<int:contract_idx>/settlements/', SettlementViewSet.as_view({'get':'list','post':'add','delete':'delete_contract'}), name='contract-settlements'),
    path('contracts/<int:contract_idx>/artifacts/', ArtifactViewSet.as_view({'get':'list','post':'add','delete':'delete_contract'}), name='contract-artifacts'),
    path('contracts/<int:contract_idx>/advances/', AdvanceViewSet.as_view({'get':'list','post':'add'}), name='advance'),
    path('contracts/<int:contract_idx>/residuals/', ResidualViewSet.as_view({'get':'list','post':'add'}), name='residual'),
    path('contracts/<int:contract_idx>/deposits/', DepositViewSet.as_view({'get':'list','post':'add'}), name='deposit'),
    path('contracts/count/', ContractViewSet.as_view({'get': 'get_contract_count'}), name='contract-count'),
    path('accounts/', AccountViewSet.as_view({'get':'list'}), name='account-list'),
    path('recipients/', RecipientViewSet.as_view({'get':'list'}), name='recipient-list'),
    path('events/', EventViewSet.as_view({'get': 'list'}), name='event-list'),  
    path('address/', AddressViewSet.as_view({'get':'get'}), name='address'),
    path('contacts/', ContactViewSet.as_view({'get':'list', 'post':'add'}), name='contact-list'),
    path('contacts/<int:contact_idx>/', ContactViewSet.as_view({'delete':'delete'}), name='contact-detail'),
    path('library/', LibraryViewSet.as_view({'get':'list'}), name='library-templates'),
    path('get-csrf-token/', get_csrf_token, name='get_csrf_token'),
]