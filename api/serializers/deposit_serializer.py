from rest_framework import serializers

class DepositSerializer(serializers.Serializer):
    settle_idx = serializers.IntegerField()
    bank = serializers.CharField(required=False, max_length=50)
    account_id = serializers.UUIDField(required=False)
    counterparty = serializers.CharField(required=False,max_length=255)
    deposit_amt = serializers.CharField(max_length=40)
    deposit_dt = serializers.DateTimeField()
    tx_hash = serializers.CharField(max_length=64) 
    dispute_reason = serializers.CharField(required=False, max_length=255)
