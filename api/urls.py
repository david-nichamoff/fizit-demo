from django.urls import path
from .views import *

urlpatterns = [
    path('contracts/<str:contract_type>/', ContractViewSet.as_view({'post':'create'}), name='contract-list'),
    path('contracts/<str:contract_type>/<int:contract_idx>/', ContractViewSet.as_view({'get':'retrieve', 'patch':'update', 'delete':'destroy'}), name='contract-detail'),
    path('contracts/<str:contract_type>/<int:contract_idx>/parties/', PartyViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-parties'),
    path('contracts/<str:contract_type>/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-transactions'),
    path('contracts/<str:contract_type>/<int:contract_idx>/settlements/', SettlementViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-settlements'),
    path('contracts/<str:contract_type>/<int:contract_idx>/artifacts/', ArtifactViewSet.as_view({'get':'list', 'post':'create', 'delete':'destroy'}), name='contract-artifacts'),
    path('contracts/<str:contract_type>/<int:contract_idx>/advances/', AdvanceViewSet.as_view({'get':'list', 'post':'create'}), name='advance'),
    path('contracts/<str:contract_type>/<int:contract_idx>/residuals/', ResidualViewSet.as_view({'get':'list', 'post':'create'}), name='residual'),
    path('contracts/<str:contract_type>/<int:contract_idx>/deposits/', DepositViewSet.as_view({'get':'list', 'post':'create'}), name='deposit'),
    path('contracts/<str:contract_type>/count/', ContractViewSet.as_view({'get': 'count'}), name='contract-count'),
    path('accounts/', AccountViewSet.as_view({'get':'list'}), name='account-list'),
    path('recipients/', RecipientViewSet.as_view({'get':'list'}), name='recipient-list'),
    path('events/', EventViewSet.as_view({'get': 'list'}), name='event-list'),  
    path('get-csrf-token/', get_csrf_token, name='get_csrf_token'),
]