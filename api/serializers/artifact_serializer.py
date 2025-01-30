from rest_framework import serializers

class ArtifactSerializer(serializers.Serializer):
    contract_type = serializers.CharField(max_length=25)
    contract_idx = serializers.IntegerField(read_only=True)
    artifact_idx = serializers.IntegerField(read_only=True)
    doc_title = serializers.CharField(max_length=50)
    doc_type = serializers.CharField(max_length=50)
    added_dt = serializers.DateTimeField()
    s3_bucket = serializers.CharField(max_length=255)  
    s3_object_key = serializers.CharField(max_length=1024) 
    s3_version_id = serializers.CharField(max_length=255) 