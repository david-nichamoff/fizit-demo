from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema

from packages.api_interface import get_advances, add_advances
from packages.check_privacy import is_master_key

from api.serializers.advance_serializer import AdvanceSerializer

from api.permissions import HasCustomAPIKey
from api.authentication import CustomAPIKeyAuthentication

class AdvanceViewSet(viewsets.ViewSet):
    authentication_classes = [SessionAuthentication , CustomAPIKeyAuthentication]
    permission_classes = [IsAuthenticated | HasCustomAPIKey]

    @extend_schema(
        tags=["Advances"],
        responses={status.HTTP_200_OK: AdvanceSerializer(many=True)},
        summary="Get Advance Amounts",
        description="Get a the current advance amounts for a contract as a list",
    )
    def list(self, request,contract_idx=None):
        try:
            advance = get_advances(int(contract_idx))
            return Response(advance, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        tags=["Advances"],
        request=AdvanceSerializer,
        responses={status.HTTP_201_CREATED: int},
        summary="Initiate Advance Payment",
        description="Initiate advance payment"
    )
    def add(self, request, contract_idx=None):
        if not is_master_key(request):
            raise PermissionDenied("You do not have permission to perform this action.")
        serializer = AdvanceSerializer(data=request.data, many=True)
        if serializer.is_valid():
            try:
                response = add_advances(int(contract_idx), serializer.validated_data)
                return Response(response, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)