from rest_framework import serializers

class ContractSerializer(serializers.Serializer):
    ext_id = serializers.JSONField()
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50)
    payment_instr = serializers.JSONField()
    funding_instr = serializers.JSONField()
    service_fee_pct = serializers.FloatField(default=0.50,min_value=0.00,max_value=1.00)
    service_fee_amt = serializers.FloatField(default=0.00,min_value=0.00)
    advance_pct = serializers.FloatField(default=0.80,min_value=0.00,max_value=1.00)
    late_fee_pct = serializers.FloatField(default=0.22,min_value=0.00,max_value=1.00)
    transact_logic = serializers.JSONField()
    is_active = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance['ext_id'] = validated_data.get('ext_id', instance['ext_id'])
        instance['contract_name'] = validated_data.get('contract_name', instance['contract_name'])
        instance['payment_instr'] = validated_data.get('payment_instr', instance['payment_instr'])
        instance['funding_instr'] = validated_data.get('funding_instr', instance['funding_instr'])
        instance['service_fee_pct'] = validated_data.get('service_fee_pct', instance['service_fee_pct'])
        instance['service_fee_amt'] = validated_data.get('service_fee_amt', instance['service_fee_amt'])
        instance['advance_pct'] = validated_data.get('advance_pct', instance['advance_pct'])
        instance['late_fee_pct'] = validated_data.get('late_fee_pct', instance['late_fee_pct'])
        instance['transact_logic'] = validated_data.get('transact_logic', instance['transact_logic'])
        instance['is_active'] = validated_data.get('is_active', instance['is_active'])
        return instance

class SettlementSerializer(serializers.Serializer):
    ext_id = serializers.JSONField()
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50)
    settle_due_dt = serializers.DateField() 
    transact_min_dt =  serializers.DateField()  
    transact_max_dt =  serializers.DateField() 
    transact_count = serializers.IntegerField(read_only=True)
    settle_pay_dt =  serializers.DateField(read_only=True) 
    settle_exp_amt = serializers.FloatField(read_only=True,default=0,min_value=0) 
    settle_pay_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    settle_confirm = serializers.CharField(read_only=True,max_length=1000)
    dispute_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    dispute_reason =  serializers.CharField(read_only=True,max_length=1000)
    days_late = serializers.IntegerField(read_only=True)
    late_fee_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    residual_pay_dt =  serializers.DateField(read_only=True)  
    residual_exp_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    residual_pay_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    residual_confirm = serializers.CharField(read_only=True,max_length=1000)
    residual_calc_amt = serializers.FloatField(read_only=True,default=0,min_value=0)

class TransactionSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    ext_id = serializers.JSONField()
    transact_dt = serializers.DateTimeField()
    transact_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    advance_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    transact_data = serializers.JSONField()
    advance_pay_dt = serializers.DateField(read_only=True)
    advance_pay_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    advance_confirm = serializers.CharField(read_only=True,max_length=1000)

class ArtifactSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    artifact_id = serializers.CharField(read_only=True,max_length=255)

class AccountSerializer(serializers.Serializer):
    account_id = serializers.UUIDField()
    account_name = serializers.CharField(max_length=255)
    available_balance = serializers.FloatField()

class RecipientSerializer(serializers.Serializer):
    recipient_id = serializers.UUIDField()
    recipient_name = serializers.CharField(max_length=255)