from rest_framework import serializers

class BaseContractSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    extended_data = serializers.JSONField()
    contract_name = serializers.CharField(max_length=50)
    funding_instr = serializers.JSONField()
    service_fee_pct = serializers.CharField(max_length=10)
    service_fee_amt = serializers.CharField(max_length=10)
    transact_logic = serializers.JSONField()
    min_threshold_amt = serializers.CharField(max_length=20)  
    max_threshold_amt = serializers.CharField(max_length=20)  
    notes = serializers.CharField(required=False)
    is_active = serializers.BooleanField(default=True)
    is_quote = serializers.BooleanField(default=False)

    def update(self, instance, validated_data):
        """Explicitly update each field for partial updates."""
        instance["extended_data"] = validated_data.get("extended_data", instance["extended_data"])
        instance["contract_name"] = validated_data.get("contract_name", instance["contract_name"])
        instance["funding_instr"] = validated_data.get("funding_instr", instance["funding_instr"])
        instance["service_fee_pct"] = validated_data.get("service_fee_pct", instance["service_fee_pct"])
        instance["service_fee_amt"] = validated_data.get("service_fee_amt", instance["service_fee_amt"])
        instance["transact_logic"] = validated_data.get("transact_logic", instance["transact_logic"])
        instance["min_threshold_amt"] = validated_data.get("min_threshold_amt", instance["min_threshold_amt"])
        instance["max_threshold_amt"] = validated_data.get("max_threshold_amt", instance["max_threshold_amt"])
        instance["notes"] = validated_data.get("notes", instance["notes"])
        instance["is_active"] = validated_data.get("is_active", instance["is_active"])
        instance["is_quote"] = validated_data.get("is_quote", instance["is_quote"])
        return instance


class AdvanceContractSerializer(BaseContractSerializer):
    """Serializer for Advance contracts, extending BaseContractSerializer."""
    def update(self, instance, validated_data):
        """Explicitly update each field for Advance contracts."""
        instance = super().update(instance, validated_data)
        return instance


class TicketingContractSerializer(BaseContractSerializer):
    """Serializer for Ticketing contracts, adding ticketing-specific fields."""
    deposit_instr = serializers.JSONField()
    service_fee_max = serializers.CharField(max_length=10)
    advance_pct = serializers.CharField(max_length=10)
    late_fee_pct = serializers.CharField(max_length=10)

    def update(self, instance, validated_data):
        """Explicitly update each field for Ticketing contracts."""
        instance = super().update(instance, validated_data)
        instance["deposit_instr"] = validated_data.get("deposit_instr", instance["deposit_instr"])
        instance["service_fee_max"] = validated_data.get("service_fee_max", instance["service_fee_max"])
        instance["advance_pct"] = validated_data.get("advance_pct", instance["advance_pct"])
        instance["late_fee_pct"] = validated_data.get("late_fee_pct", instance["late_fee_pct"])
        return instance