from django.urls import path, re_path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('', views.index, name='index'),  
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'), 
    path('logout/', auth_views.LogoutView.as_view(next_page='index'), name='logout'),  
    path('register/', views.register_view, name='register'),
    path('user/', views.get_user, name='get_user'),
    re_path(r'^.*$', TemplateView.as_view(template_name='index.html')),
]