from rest_framework import serializers

class AdvanceSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField()
    transact_idx = serializers.IntegerField()
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField(required=False)
    recipient_id = serializers.UUIDField(required=False)
    funder_addr = serializers.CharField(required=False,max_length=42)
    recipient_addr = serializers.CharField(required=False,max_length=42)
    token_symbol = serializers.CharField(required=False,max_length=10)
    advance_amt = serializers.CharField(max_length=20)
