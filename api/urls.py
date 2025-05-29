from django.urls import path

from api.views import (
    ContractViewSet, AccountViewSet, RecipientViewSet,
    PartyViewSet, TransactionViewSet, SettlementViewSet,
    ArtifactViewSet, AdvanceViewSet, ResidualViewSet,
    DistributionViewSet, DepositViewSet, EventViewSet,
    StatsView, get_csrf_token
)

urlpatterns = [

    # **Purchase Contract Endpoints**
    path('contracts/purchase/', ContractViewSet.as_view({'post': 'create_purchase_contract'}), name='create-purchase-contract'),
    path('contracts/purchase/<int:contract_idx>/', ContractViewSet.as_view({'get': 'retrieve_purchase_contract', 'patch': 'update_purchase_contract', 'delete': 'destroy_purchase_contract'}), name='purchase-contract-detail'),
    path('contracts/purchase/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get': 'list_purchase_transactions', 'post': 'create_purchase_transactions', 'delete' : 'destroy_purchase_transactions'}), name='purchase-contract-transactions'),
    path('contracts/purchase/<int:contract_idx>/advances/', AdvanceViewSet.as_view({'get': 'list_purchase_advances', 'post': 'create_purchase_advances'}), name='purchase-contract-advances'),

    # **Sale Contract Endpoints**
    path('contracts/sale/', ContractViewSet.as_view({'post': 'create_sale_contract'}), name='create-sale-contract'),
    path('contracts/sale/<int:contract_idx>/', ContractViewSet.as_view({'get': 'retrieve_sale_contract', 'patch': 'update_sale_contract', 'delete': 'destroy_sale_contract'}), name='sale-contract-detail'),
    path('contracts/sale/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get': 'list_sale_transactions', 'post': 'create_sale_transactions', 'delete': 'destroy_sale_transactions'}), name='sale-contract-transactions'),
    path('contracts/sale/<int:contract_idx>/settlements/', SettlementViewSet.as_view({'get': 'list_sale_settlements', 'post': 'create_sale_settlements', 'delete': 'destroy_sale_settlements'}), name='sale-contract-settlements'),
    path('contracts/sale/<int:contract_idx>/distributions/', DistributionViewSet.as_view({'get': 'list_sale_distributions', 'post': 'create_sale_distributions'}), name='sale-contract-distributions'),
    path('contracts/sale/<int:contract_idx>/deposits/', DepositViewSet.as_view({'get': 'list_sale_deposits', 'post': 'create_sale_deposits'}), name='sale-contract-deposits'),

    # **Advance Contract Endpoints**
    path('contracts/advance/', ContractViewSet.as_view({'post': 'create_advance_contract'}), name='create-advance-contract'),
    path('contracts/advance/<int:contract_idx>/', ContractViewSet.as_view({'get': 'retrieve_advance_contract', 'patch': 'update_advance_contract', 'delete': 'destroy_advance_contract'}), name='advance-contract-detail'),
    path('contracts/advance/<int:contract_idx>/transactions/', TransactionViewSet.as_view({'get': 'list_advance_transactions', 'post': 'create_advance_transactions', 'delete':'destroy_advance_transactions'}), name='advance-contract-transactions'),
    path('contracts/advance/<int:contract_idx>/settlements/', SettlementViewSet.as_view({'get': 'list_advance_settlements', 'post': 'create_advance_settlements', 'delete': 'destroy_advance_settlements'}), name='advance-contract-settlements'),
    path('contracts/advance/<int:contract_idx>/advances/', AdvanceViewSet.as_view({'get': 'list_advance_advances', 'post': 'create_advance_advances'}), name='advance-contract-advances'),
    path('contracts/advance/<int:contract_idx>/residuals/', ResidualViewSet.as_view({'get': 'list_advance_residuals', 'post': 'create_advance_residuals'}), name='advance-contract-residuals'),
    path('contracts/advance/<int:contract_idx>/deposits/', DepositViewSet.as_view({'get': 'list_advance_deposits', 'post': 'create_advance_deposits'}), name='advance-contract-deposits'),

    # **Standard Contract Endpoints**
    path('contracts/', ContractViewSet.as_view({'get': 'list_contracts'}), name='list-contracts'),
    path('contracts/<str:party_code>/', ContractViewSet.as_view({'get': 'list_contracts_by_party_code'}), name='list-contracts-by-party-code'),
    path('contracts/<str:contract_type>/count/', ContractViewSet.as_view({'get': 'count_contract'}), name='contract-count'),
    path('contracts/<str:contract_type>/<int:contract_idx>/parties/', PartyViewSet.as_view({'get': 'list_parties', 'post': 'create_parties', 'delete': 'destroy_parties'}), name='contract-parties'),
    path('contracts/<str:contract_type>/<int:contract_idx>/<str:party_idx>/approve/', PartyViewSet.as_view({'post': 'approve_party'}), name='approve-party'),
    path('contracts/<str:contract_type>/<int:contract_idx>/artifacts/', ArtifactViewSet.as_view({'get': 'list_artifacts', 'post': 'create_artifacts', 'delete': 'destroy_artifacts'}), name='contract-artifacts'),
    
    # **General Endpoints**
    path('accounts/', AccountViewSet.as_view({'get': 'list'}), name='account-list'),
    path('recipients/', RecipientViewSet.as_view({'get': 'list'}), name='recipient-list'),
    path('events/', EventViewSet.as_view({'get': 'list'}), name='event-list'),
    path('stats/', StatsView.as_view(), name='stats'),
    path('get-csrf-token/', get_csrf_token, name='get_csrf_token'),
]