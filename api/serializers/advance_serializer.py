from rest_framework import serializers

class AdvanceSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField()
    contract_name = serializers.CharField(required=False,max_length=255)
    transact_idx = serializers.IntegerField()
    transact_dt = serializers.DateTimeField(required=False)
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField(required=False)
    account_name = serializers.CharField(required=False,max_length=255)
    recipient_id = serializers.UUIDField(required=False)
    recipient_name = serializers.CharField(required=False,max_length=255)
    funder_addr = serializers.CharField(required=False,max_length=42)
    funder_party_code = serializers.CharField(required=False,max_length=20)
    recipient_addr = serializers.CharField(required=False,max_length=42)
    recipient_party_code = serializers.CharField(required=False,max_length=20)
    token_symbol = serializers.CharField(required=False,max_length=10)
    advance_amt = serializers.CharField(max_length=20)
