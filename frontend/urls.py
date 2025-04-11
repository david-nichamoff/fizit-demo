from django.urls import path, re_path
from django.views.generic import TemplateView
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect

from .views import get_user, oidc_logout, whoami 

def redirect_to_oidc_login(request):
    return redirect('/oidc/authenticate/')  # Default path for mozilla-django-oidc

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login/', redirect_to_oidc_login, name='login'),
    path('logout/', oidc_logout, name='logout'),  
    path('user/', get_user, name='get_user'),  
    path("whoami/", whoami),
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]