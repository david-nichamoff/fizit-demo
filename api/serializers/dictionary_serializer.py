from rest_framework import serializers

from api.models.dictionary_models import DataDictionary

class DictionarySerializer(serializers.ModelSerializer):
    class Meta:
        model = DataDictionary
        fields = ['type', 'field_code', 'language_code', 'display_name']