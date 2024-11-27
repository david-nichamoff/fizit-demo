from rest_framework import serializers

from api.models.event_models import Event

class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event 
        fields = ['event_idx', 'contract_idx', 'network', 'from_addr', 'to_addr', 'tx_hash', 'gas_used', 'event_type', 'event_dt', 'details', 'status']