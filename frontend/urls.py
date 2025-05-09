from django.urls import path, re_path
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.http import HttpResponse

from .views.common import get_user, oidc_logout, whoami 
from .views.dashboard import list_contracts_view, view_contract_view
from .views.dashboard.auth import DashboardLoginView, DashboardLogoutView

def redirect_to_oidc_login(request):
    return redirect('/oidc/authenticate/')  # Default path for mozilla-django-oidc

urlpatterns = [
    path("login/", DashboardLoginView.as_view(), name="dashboard_login"),
    path("logout/", DashboardLogoutView.as_view(), name="dashboard_logout"),
    path("register/", lambda request: HttpResponse("Registration not implemented."), name="register"),


    path('google-login/', redirect_to_oidc_login, name='google_login'),
    path('user/', get_user, name='get_user'),  
    path("whoami/", whoami),

    path('<str:customer>/view-contract/', view_contract_view, name='view_contract'),
    path('<str:customer>/', list_contracts_view, name='list_contracts'),
]