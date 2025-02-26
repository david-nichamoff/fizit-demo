from rest_framework import serializers

class BaseTransactionSerializer(serializers.Serializer):
    contract_type = serializers.CharField(read_only=True, max_length=25)
    contract_idx = serializers.IntegerField(read_only=True)
    transact_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    extended_data = serializers.JSONField()
    transact_dt = serializers.DateTimeField()
    transact_amt = serializers.CharField(max_length=20, default = "0.00")
    transact_data = serializers.JSONField()

class PurchaseTransactionSerializer(BaseTransactionSerializer):
    funding_instr = serializers.CharField(read_only=True)
    service_fee_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_pay_dt = serializers.DateTimeField(read_only=True)
    advance_pay_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_tx_hash = serializers.CharField(read_only=True, max_length=64) 

class SaleTransactionSerializer(BaseTransactionSerializer):
    pass

class AdvanceTransactionSerializer(BaseTransactionSerializer):
    funding_instr = serializers.CharField(read_only=True)
    service_fee_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_pay_dt = serializers.DateTimeField(read_only=True)
    advance_pay_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_tx_hash = serializers.CharField(read_only=True, max_length=64) 