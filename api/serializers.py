from rest_framework import serializers

from .models import DataDictionary, ContractEvent

class ContractSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    extended_data = serializers.JSONField()
    contract_name = serializers.CharField(max_length=50)
    contract_type = serializers.CharField(max_length=50)
    funding_instr = serializers.JSONField()
    service_fee_pct = serializers.FloatField(default=0.50,min_value=0.00,max_value=1.00)
    service_fee_max = serializers.FloatField(default=0.50,min_value=0.00,max_value=1.00)
    service_fee_amt = serializers.FloatField(default=0.00,min_value=0.00)
    advance_pct = serializers.FloatField(default=0.80,min_value=0.00,max_value=1.00)
    late_fee_pct = serializers.FloatField(default=0.22,min_value=0.00,max_value=1.00)
    transact_logic = serializers.JSONField()
    notes = serializers.CharField(max_length=255)
    is_active = serializers.BooleanField()
    is_quote = serializers.BooleanField()

    def update(self, instance, validated_data):
        instance['extended_data'] = validated_data.get('extended_data', instance['extended_data'])
        instance['contract_name'] = validated_data.get('contract_name', instance['contract_name'])
        instance['contract_type'] = validated_data.get('contract_type', instance['contract_name'])
        instance['funding_instr'] = validated_data.get('funding_instr', instance['funding_instr'])
        instance['service_fee_pct'] = validated_data.get('service_fee_pct', instance['service_fee_pct'])
        instance['service_fee_max'] = validated_data.get('service_fee_max', instance['service_fee_max'])
        instance['service_fee_amt'] = validated_data.get('service_fee_amt', instance['service_fee_amt'])
        instance['advance_pct'] = validated_data.get('advance_pct', instance['advance_pct'])
        instance['late_fee_pct'] = validated_data.get('late_fee_pct', instance['late_fee_pct'])
        instance['transact_logic'] = validated_data.get('transact_logic', instance['transact_logic'])
        instance['notes'] = validated_data.get('notes', instance['notes'])
        instance['is_active'] = validated_data.get('is_active', instance['is_active'])
        instance['is_quote'] = validated_data.get('is_quote', instance['is_quote'])
        return instance

class PartySerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    party_idx = serializers.IntegerField(read_only=True)
    party_code = serializers.CharField(max_length=50)
    party_type = serializers.CharField(max_length=50)

class SettlementSerializer(serializers.Serializer):
    extended_data = serializers.JSONField()
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(read_only=True, max_length=50)
    funding_instr = serializers.JSONField(read_only=True)
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
    funding_instr = serializers.JSONField(read_only=True)
    extended_data = serializers.JSONField()
    transact_dt = serializers.DateTimeField()
    transact_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    advance_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    transact_data = serializers.JSONField()
    advance_pay_dt = serializers.DateField(read_only=True)
    advance_pay_amt = serializers.FloatField(read_only=True,default=0,min_value=0)
    advance_confirm = serializers.CharField(read_only=True,max_length=1000)

class TicketSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    ticket_data = serializers.JSONField()
    ticket_id = serializers.IntegerField()
    approved_dt = serializers.DateField()
    ticket_amt = serializers.FloatField()

class InvoiceSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    invoice_data = serializers.JSONField()
    invoice_id = serializers.IntegerField()

class DepositSerializer(serializers.Serializer):
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField()
    deposit_id = serializers.UUIDField()
    counterparty = serializers.CharField(max_length=255)
    deposit_amt = serializers.FloatField()
    deposit_dt = serializers.DateField()

class ArtifactSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    artifact_id = serializers.CharField(read_only=True,max_length=255)
    doc_title = serializers.CharField(max_length=50)
    doc_type = serializers.CharField(max_length=50)
    added_dt = serializers.DateField()

class AccountSerializer(serializers.Serializer):
    bank = serializers.CharField(max_length=50)
    account_id = serializers.UUIDField()
    account_name = serializers.CharField(max_length=255)
    available_balance = serializers.FloatField()

class RecipientSerializer(serializers.Serializer):
    bank = serializers.CharField(max_length=50)
    recipient_id = serializers.UUIDField()
    recipient_name = serializers.CharField(max_length=255)

class DataDictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDictionary
        fields = ['type', 'field_code', 'language_code', 'display_name']

class ContractEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContractEvent 
        fields = ['event_idx', 'contract_idx', 'event_type', 'details', 'event_dt']