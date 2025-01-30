from rest_framework import serializers

class TransactionSerializer(serializers.Serializer):
    contract_type = serializers.CharField(read_only=True, max_length=25)
    contract_idx = serializers.IntegerField(read_only=True)
    transact_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    extended_data = serializers.JSONField()
    funding_instr = serializers.CharField(read_only=True)
    transact_dt = serializers.DateTimeField()
    transact_amt = serializers.CharField(max_length=20, default = "0.00")
    service_fee_amt = serializers.CharField(max_length=20, default = "0.00")
    advance_amt = serializers.CharField(max_length=20, default = "0.00")
    transact_data = serializers.JSONField()
    advance_pay_dt = serializers.DateTimeField(read_only=True)
    advance_pay_amt = serializers.CharField(max_length=20, default = "0.00")
    advance_tx_hash = serializers.CharField(max_length=64, read_only=True) 