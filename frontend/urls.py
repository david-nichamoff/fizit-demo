from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),  # Update to point to homepage view
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'), 
    path('logout/', auth_views.LogoutView.as_view(next_page='homepage'), name='logout'),  # Redirect to homepage after logout
    path('register/', views.register_view, name='register'),
    path('user/', views.get_user, name='get_user')
]