from django.urls import path, re_path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from .views.common import get_user, oidc_logout, whoami 
from .views.dashboard import list_contracts_view, view_contract_view

def redirect_to_oidc_login(request):
    return redirect('/oidc/authenticate/')  # Default path for mozilla-django-oidc

urlpatterns = [
    path('login/', redirect_to_oidc_login, name='login'),
    path('logout/', oidc_logout, name='logout'),  
    path('user/', get_user, name='get_user'),  
    path("whoami/", whoami),

    path('<str:customer>/', list_contracts_view, name='list_contracts'),
    path('<str:customer>/view-contract/', view_contract_view, name='view_contract'),

]