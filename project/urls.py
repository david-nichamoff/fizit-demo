from django.urls import path, include
from django.contrib import admin
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings
from django.conf.urls.static import static
from django.views.decorators.csrf import csrf_exempt

from rest_framework.permissions import AllowAny
from api.authentication import NoAuthForSwagger

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')), 
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

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

    path("", include("frontend.urls")),  
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)