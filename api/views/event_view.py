import logging

from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import viewsets, status

from drf_spectacular.utils import extend_schema, OpenApiParameter

from api.serializers.event_serializer import EventSerializer
from api.models import Event
from api.authentication import AWSSecretsAPIKeyAuthentication
from api.permissions import HasCustomAPIKey
from api.views.mixins.validation import ValidationMixin
from api.utilities.logging import log_info, log_warning, log_error

class EventViewSet(viewsets.ViewSet, ValidationMixin):
    """
    A ViewSet for managing event-related operations.
    """
    authentication_classes = [AWSSecretsAPIKeyAuthentication]
    permission_classes = [HasCustomAPIKey]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)

    @extend_schema(
        tags=["Events"],
        parameters=[
            OpenApiParameter(name='contract_idx', description='Contract index for filtering events', required=False, type=int),
            OpenApiParameter(name='contract_type', description='Contract type for filtering events', required=False, type=str),
            OpenApiParameter(name='from_addr', description='Source address for filtering events', required=False, type=str),
            OpenApiParameter(name='to_addr', description='Destination address for filtering events', required=False, type=str),
        ],
        summary="List Events",
        description="Retrieve the list of events with optional filters.",
        responses={status.HTTP_200_OK: EventSerializer(many=True)},
    )
    def list(self, request):
        """
        Retrieve a list of events filtered by optional query parameters.
        """
        log_info(self.logger, f"Listing events with query parameters: {request.query_params}")

        try:
            # Filter events
            queryset = self._filter_queryset(request.query_params)
            serializer = EventSerializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except ValidationError as e:
            log_error(self.logger, f"Validation error: {str(e)}")
            return Response({"error": f"Validation error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_error(self.logger, f"Unexpected error: {str(e)}")
            return Response({"error": f"Unexpected error {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _filter_queryset(self, query_params):
        """
        Apply filters to the Event queryset based on query parameters.
        """
        queryset = Event.objects.all()

        if contract_idx := query_params.get('contract_idx'):
            queryset = queryset.filter(contract_idx=contract_idx)

        if contract_type := query_params.get('contract_type'):
            queryset = queryset.filter(contract_type=contract_type)

        if from_addr := query_params.get('from_addr'):
            queryset = queryset.filter(from_addr=from_addr)

        if to_addr := query_params.get('to_addr'):
            queryset = queryset.filter(to_addr=to_addr)

        log_info(self.logger, f"Filtered queryset count: {queryset.count()}")
        return queryset