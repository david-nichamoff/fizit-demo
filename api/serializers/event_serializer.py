from rest_framework import serializers

from api.models.event_models import ContractEvent

class ContractEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractEvent 
        fields = ['event_idx', 'contract_idx', 'contract_addr', 'event_type', 'details', 'event_dt']