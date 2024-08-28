from rest_framework import serializers

class ResidualSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    settle_idx = serializers.IntegerField(read_only=True)
    bank = serializers.CharField(read_only=True,max_length=50)
    account_id = serializers.UUIDField(read_only=True)
    recipient_id = serializers.UUIDField(read_only=True)
    residual_exp_amt = serializers.CharField(max_length=20)