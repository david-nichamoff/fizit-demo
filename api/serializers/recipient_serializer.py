from rest_framework import serializers

class RecipientSerializer(serializers.Serializer):
    bank = serializers.CharField(max_length=50)
    recipient_id = serializers.UUIDField()
    recipient_name = serializers.CharField(max_length=255)