from rest_framework import serializers

class ApprovalSerializer(serializers.Serializer):
    approved_user = serializers.CharField(max_length=150, default='fizit')