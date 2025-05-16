from django.urls import path
from django.contrib.auth import views as auth_views
from django.http import HttpResponse

from .views.dashboard.docusign_view import docusign_callback, start_docusign_auth
from .views.dashboard.change_password_view import change_password_view

from .views.dashboard import (
    list_contracts_view, view_contract_view, approve_contract_view, register_view,
    DashboardLoginView, DashboardLogoutView
)

urlpatterns = [
    path("login/", DashboardLoginView.as_view(), name="dashboard_login"),
    path("logout/", DashboardLogoutView.as_view(), name="dashboard_logout"),
    path("register/", register_view, name="register"),
    path('change_password/', change_password_view, name='change_password'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='dashboard/password_change_done.html'), name='password_change_done'),
    path('<str:customer>/view-contract/', view_contract_view, name='view_contract'),
    path('<str:customer>/', list_contracts_view, name='list_contracts'),
    path("docusign/start/", start_docusign_auth, name="docusign_start"),
    path("docusign/callback/", docusign_callback, name="docusign_callback"),
    path("<str:customer>/approve/<str:contract_type>/<int:contract_idx>/<str:contract_release>/", approve_contract_view, name="approve_contract")
]