import logging

from rest_framework.response import Response
from rest_framework import viewsets, status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.event_serializer import EventSerializer
from api.models import Event

from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey

logger = logging.getLogger(__name__)

class EventViewSet(viewsets.ViewSet):
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.logger = logging.getLogger(__name__)
        self.initialized = True  # Mark this instance as initialized

    @extend_schema(
        tags=["Events"],
        parameters=[
            OpenApiParameter(name='contract_idx', description='Contract_idx for filtering contract events', required=False, type=int),
            OpenApiParameter(name='from_addr', description='Contract address for filtering contract events', required=False, type=str),
            OpenApiParameter(name='to_addr', description='Contract address for filtering contract events', required=False, type=str),
        ],
        summary="List Events",
        description="Retrieve the list of events"
    )
    def list(self, request):
        try:
            contract_idx = request.query_params.get('contract_idx')
            from_addr = request.query_params.get('from_addr')
            to_addr = request.query_params.get('to_addr')
            queryset = Event.objects.all()

            if contract_idx:
                queryset = queryset.filter(contract_idx=contract_idx)
            if from_addr:
                queryset = queryset.filter(from_addr=from_addr)
            if to_addr:
                queryset = queryset.filter(to_addr=to_addr)

            serializer = EventSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ValueError as ve:
            self.logger.error(f"Invalid query parameter: {str(ve)}")
            return Response({"error": f"Invalid query parameter: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"Error retrieving events: {str(e)}")
            return Response({"error": "An error occurred while retrieving events."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)