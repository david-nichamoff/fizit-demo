from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema

class StatsView(APIView):

    @extend_schema(
        tags=["Stats"],
        summary="Transaction Stats",
        description="Retrieve transaction statistics",
    )
    def get(self, request):
        transaction_value = 500000  # Example value

        return Response({"value": transaction_value}, status=status.HTTP_200_OK)