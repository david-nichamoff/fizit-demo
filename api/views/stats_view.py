from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny 

from api.authentication import AWSSecretsAPIKeyAuthentication  
from api.permissions import HasCustomAPIKey  
from api.managers.cache_manager import CacheManager

class StatsView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Admin"],
        summary="Transaction Stats",
        description="Retrieve transaction statistics",
    )
    def get(self, request):
        cache_manager = CacheManager()
        stats = cache_manager.get(cache_manager.get_stats_cache_key(), 0)  
        return Response(stats, status=status.HTTP_200_OK)
