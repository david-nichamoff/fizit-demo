from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny 


from api.authentication import AWSSecretsAPIKeyAuthentication  
from api.permissions import HasCustomAPIKey  

class StatsView(APIView):
    authentication_classes = [] 
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Stats"],
        summary="Transaction Stats",
        description="Retrieve transaction statistics",
    )
    def get(self, request):
        transaction_value = 500000  # Example value
        return Response({"value": transaction_value}, status=status.HTTP_200_OK)