from rest_framework import serializers

class ResidualSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField()
    settle_idx = serializers.IntegerField()
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField()
    recipient_id = serializers.UUIDField()
    residual_calc_amt = serializers.CharField(max_length=20)