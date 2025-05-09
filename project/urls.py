from django.urls import path, include, re_path
from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponsePermanentRedirect
from django.shortcuts import redirect
from django.views.generic import TemplateView

from rest_framework.permissions import AllowAny
from api.authentication import NoAuthForSwagger

from frontend.admin.custom_admin_site import custom_admin_site
from frontend.views.common import oidc_logout 

def redirect_to_oidc(request):
    return redirect('/oidc/authenticate/')

urlpatterns = [
    re_path(r'^admin$', lambda request: HttpResponsePermanentRedirect('/admin/')),

    path('admin/', custom_admin_site.urls),
    path('api/', include('api.urls')),

    path('api/schema/', csrf_exempt(SpectacularAPIView.as_view(
        authentication_classes=[NoAuthForSwagger],
        permission_classes=[AllowAny]
    )), name='schema'),

    path('api/schema/swagger-ui/', csrf_exempt(SpectacularSwaggerView.as_view(
        url_name='schema',
        authentication_classes=[NoAuthForSwagger],  # Use no authentication for Swagger UI
        permission_classes=[AllowAny]
    )), name='swagger-ui'),

    path('api/schema/redoc/', csrf_exempt(SpectacularRedocView.as_view(
        url_name='schema',
        authentication_classes=[NoAuthForSwagger],  # No authentication for Redoc as well
        permission_classes=[AllowAny]
    )), name='redoc'),

    path('oidc/', include('mozilla_django_oidc.urls')),
    path('accounts/login/', redirect_to_oidc),
    path("logout/", oidc_logout, name="logout"), 

    path("dashboard/", include("frontend.urls")),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
    re_path(r'^(?!api/|admin/|oidc/|dashboard/).*$',
        TemplateView.as_view(template_name='index.html')),
]
