from rest_framework import serializers

from api.models.event_models import Event

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event 
        fields = ['event_idx', 'contract_idx', 'contract_addr', 'event_type', 'details', 'event_dt']