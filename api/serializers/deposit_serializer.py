from rest_framework import serializers

class DepositSerializer(serializers.Serializer):
    settle_idx = serializers.IntegerField()
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField()
    deposit_id = serializers.UUIDField()
    counterparty = serializers.CharField(max_length=255)
    deposit_amt = serializers.CharField(max_length=40)
    deposit_dt = serializers.DateTimeField()
    dispute_reason = serializers.CharField(max_length=255)
    settle_confirm = serializers.CharField(max_length=255)
