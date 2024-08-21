from rest_framework import serializers

class ArtifactSerializer(serializers.Serializer):
    contract_idx = serializers.IntegerField(read_only=True)
    artifact_idx = serializers.IntegerField(read_only=True)
    contract_name = serializers.CharField(max_length=50, read_only=True)
    artifact_id = serializers.CharField(read_only=True,max_length=255)
    doc_title = serializers.CharField(max_length=50)
    doc_type = serializers.CharField(max_length=50)
    added_dt = serializers.DateTimeField()