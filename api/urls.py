from django.urls import path
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('contracts/', views.ContractViewSet.as_view({'get': 'list', 'post': 'create'}), name='contract-list'),
    path('contracts/<int:contract_idx>/', views.ContractViewSet.as_view({'get': 'get', 'patch': 'partial_update'}), name='contract-detail'),
    path('contracts/<int:contract_idx>/pay-advance/', views.ContractViewSet.as_view({'post':'pay_advance'}), name='pay-advance'),
    path('contracts/<int:contract_idx>/pay-residual/', views.ContractViewSet.as_view({'post':'pay_residual'}), name='pay-residual'),
    path('contracts/<int:contract_idx>/post-settlement/', views.ContractViewSet.as_view({'post':'post_settlement'}), name='post-settlement'),
    path('contracts/<int:contract_idx>/get-deposits/<str:date_from>/', views.ContractViewSet.as_view({'post':'get_deposits'}), name='get-deposits'),
    path('contracts/<int:contract_idx>/settlements/', views.SettlementViewSet.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='contract-settlements'),
    path('contracts/<int:contract_idx>/artifacts/', views.ArtifactViewSet.as_view({'get': 'list', 'post':'create','delete': 'delete'}), name='contract-artifacts'),
    path('contracts/<int:contract_idx>/transactions/', views.TransactionViewSet.as_view({'get': 'list', 'post': 'create', 'delete': 'delete'}), name='contract-transactions'),
    path('transactions/', views.TransactionViewSet.as_view({'get': 'list'}), name='transaction-list'),
    path('settlements/', views.SettlementViewSet.as_view({'get': 'list'}), name='settlement-list'),
    path('artifacts/', views.ArtifactViewSet.as_view({'get': 'list'}), name='artifact-list'),
    path('accounts/', views.AccountViewSet.as_view({'get': 'list'}), name='account-list'),
    path('recipients/', views.RecipientViewSet.as_view({'get': 'list'}), name='recipient-list'),
]