from django.urls import path
from dashboard.views import list_contracts_view, view_contract_view

urlpatterns = [
    path('<str:customer>/', list_contracts_view, name='list_contracts'),
    path('<str:customer>/view-contract/', view_contract_view, name='view_contract')
]