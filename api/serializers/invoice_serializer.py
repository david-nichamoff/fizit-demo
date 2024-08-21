from rest_framework import serializers

class InvoiceSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    invoice_data = serializers.JSONField()
    invoice_id = serializers.IntegerField()