from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny 

from django.core.cache import cache

from api.authentication import AWSSecretsAPIKeyAuthentication  
from api.permissions import HasCustomAPIKey  
from api.cache import CacheManager

class StatsView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Stats"],
        summary="Transaction Stats",
        description="Retrieve transaction statistics",
    )
    def get(self, request):
        cache_manager = CacheManager()

        stats = cache.get(cache_manager.get_stats_cache_key(), {'total_advance_amt': 0.00})  
        total_advance_amt = round(stats.get('total_advance_amt', 0.00))
        return Response({"total_advance_amt": total_advance_amt}, status=status.HTTP_200_OK)