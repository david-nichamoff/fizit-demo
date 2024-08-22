from rest_framework import serializers

class ResidualSerializer(serializers.Serializer):
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField()
    account_name = serializers.CharField(max_length=255)
    available_balance = serializers.CharField(max_length=20)
    residual_pay_amt = serializers.CharField(max_length=20)