from rest_framework import serializers

class DistributionSerializer(serializers.Serializer):
    contract_type = serializers.CharField(max_length=25)
    contract_idx = serializers.IntegerField()
    contract_name = serializers.CharField(required=False,max_length=255)
    settle_idx = serializers.IntegerField()
    settle_due_dt = serializers.DateTimeField(required=False) 
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField(required=False)
    recipient_id = serializers.UUIDField(required=False)
    funder_addr = serializers.CharField(required=False,max_length=42)
    recipient_addr = serializers.CharField(required=False,max_length=42)
    network = serializers.CharField(required=False, max_length=20)
    token_symbol = serializers.CharField(required=False,max_length=10)
    tx_hash = serializers.CharField(required=False, max_length=66) 
    distribution_calc_amt = serializers.CharField(max_length=20)