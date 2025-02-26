from rest_framework import serializers

class BaseSettlementSerializer(serializers.Serializer):
    contract_type = serializers.CharField(read_only=True, max_length=25)
    contract_idx = serializers.IntegerField(read_only=True)
    settle_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(read_only=True, max_length=50)
    extended_data = serializers.JSONField()
    funding_instr = serializers.CharField(read_only=True)
    deposit_instr = serializers.CharField(read_only=True)
    settle_due_dt = serializers.DateTimeField() 
    settle_pay_dt =  serializers.DateTimeField(read_only=True) 
    settle_pay_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    settle_tx_hash = serializers.CharField(read_only=True, max_length=64, required=False)
    days_late = serializers.IntegerField(read_only=True)
    late_fee_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")

class SaleSettlementSerializer(BaseSettlementSerializer):
    principal_amt = serializers.CharField(max_length=20, default = "0.00")
    settle_exp_amt = serializers.CharField(max_length=20, default = "0.00")
    dist_pay_dt =  serializers.DateTimeField(read_only=True)  
    dist_pay_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    dist_calc_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    dist_tx_hash = serializers.CharField(read_only=True, max_length=64, required=False)

class AdvanceSettlementSerializer(BaseSettlementSerializer):
    transact_min_dt =  serializers.DateTimeField()  
    transact_max_dt =  serializers.DateTimeField() 
    transact_count = serializers.IntegerField(read_only=True)
    settle_exp_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    advance_amt_gross = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    dispute_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    dispute_reason =  serializers.CharField(read_only=True, max_length=1000)
    residual_pay_dt =  serializers.DateTimeField(read_only=True)  
    residual_exp_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    residual_pay_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    residual_calc_amt = serializers.CharField(read_only=True, max_length=20, default = "0.00")
    residual_tx_hash = serializers.CharField(read_only=True, max_length=64, required=False)
   