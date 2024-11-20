from rest_framework import serializers

class AdvanceSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField()
    transact_idx = serializers.IntegerField()
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField(required=False)
    recipient_id = serializers.UUIDField(required=False)
    party_addr = serializers.CharField(read_only=True,max_length=42)
    advance_amt = serializers.CharField(max_length=20)
