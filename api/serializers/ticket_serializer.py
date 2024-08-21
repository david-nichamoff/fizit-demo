from rest_framework import serializers

class TicketSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    ticket_data = serializers.JSONField()
    ticket_id = serializers.IntegerField()
    approved_dt = serializers.DateTimeField()
    ticket_amt = serializers.CharField(max_length=20)