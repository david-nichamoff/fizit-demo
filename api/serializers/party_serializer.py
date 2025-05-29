from rest_framework import serializers

class PartySerializer(serializers.Serializer):
    contract_type = serializers.CharField(read_only=True, max_length=25)
    contract_idx = serializers.IntegerField(read_only=True)
    party_idx = serializers.IntegerField(read_only=True)
    party_code = serializers.CharField(max_length=20)
    party_type = serializers.CharField(max_length=10)
    party_addr = serializers.CharField(read_only=True,max_length=42)
    approved_dt = serializers.DateTimeField(read_only=True)
    approved_user = serializers.CharField(max_length=150, read_only=True)