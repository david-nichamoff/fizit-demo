from django.urls import path
from . import views

urlpatterns = [
    path('contracts/', views.ContractViewSet.as_view({'get':'list','post':'create'}), name='contract-list'),
    path('contracts/<int:contract_idx>/', views.ContractViewSet.as_view({'get':'retrieve','patch':'partial_update'}), name='contract-detail'),
    path('contracts/<int:contract_idx>/parties/', views.PartyViewSet.as_view({'get':'list_contract','post':'create','delete':'delete'}), name='contract-parties'),
    path('contracts/<int:contract_idx>/transactions/', views.TransactionViewSet.as_view({'get':'list_contract','post':'create','delete':'delete'}), name='contract-transactions'),
    path('contracts/<int:contract_idx>/tickets/', views.TicketViewSet.as_view({'get':'list_contract','post':'process'}), name='contract-tickets'),
    path('contracts/<int:contract_idx>/settlements/', views.SettlementViewSet.as_view({'get':'list_contract','post':'create','delete':'delete'}), name='contract-settlements'),
    path('contracts/<int:contract_idx>/artifacts/', views.ArtifactViewSet.as_view({'get':'list_contract','post':'create','delete':'delete'}), name='contract-artifacts'),
    path('transactions/', views.TransactionViewSet.as_view({'get':'list','post':'create'}), name='transaction-list'),
    path('settlements/', views.SettlementViewSet.as_view({'get':'list'}), name='settlement-list'),
    path('accounts/', views.AccountViewSet.as_view({'get':'list'}), name='account-list'),
    path('accounts/<str:account_id>/pay-advance/', views.AccountViewSet.as_view({'post':'pay_advance'}), name='pay-advance'),
    path('accounts/<str:account_id>/pay-residual/', views.AccountViewSet.as_view({'post':'pay_residual'}), name='pay-residual'),
    path('accounts/<str:account_id>/post-settlement/', views.AccountViewSet.as_view({'post':'post_settlement'}), name='post-settlement'),
    path('accounts/<str:account_id>/deposits/', views.DepositViewSet.as_view({'get':'list'}), name='deposit-list'),
    path('recipients/', views.RecipientViewSet.as_view({'get':'list'}), name='recipient-list'),
    path('data-dictionary/', views.DataDictionaryViewSet.as_view({'get': 'list'}), name='data-dictionary-list'),  
]