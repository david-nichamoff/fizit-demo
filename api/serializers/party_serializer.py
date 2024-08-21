from rest_framework import serializers

class PartySerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    party_idx = serializers.IntegerField(read_only=True)
    party_code = serializers.CharField(max_length=20)
    party_type = serializers.CharField(max_length=10)
    party_address = serializers.CharField(read_only=True,max_length=42)