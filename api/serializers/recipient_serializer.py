from rest_framework import serializers

class RecipientSerializer(serializers.Serializer):
    bank = serializers.CharField(max_length=50)
    recipient_id = serializers.UUIDField()
    recipient_name = serializers.CharField(max_length=255)
    payment_method = serializers.CharField(max_length=50, required=False)
    account_number = serializers.CharField(max_length=50, required=False)
    routing_number = serializers.CharField(max_length=50, required=False)
    bank_name = serializers.CharField(max_length=50, required=False)
    address_1 = serializers.CharField(max_length=50, required=False)
    address_2  = serializers.CharField(max_length=50, required=False)
    city = serializers.CharField(max_length=50, required=False)
    region = serializers.CharField(max_length=50, required=False)
    postal_code = serializers.CharField(max_length=50, required=False)
    country = serializers.CharField(max_length=50, required=False)