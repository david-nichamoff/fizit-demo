from rest_framework import serializers

class AdvanceSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField()
    transact_idx = serializers.IntegerField()
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField()
    recipient_id = serializers.UUIDField()
    advance_amt = serializers.CharField(max_length=20)
