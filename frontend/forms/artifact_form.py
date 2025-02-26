import logging

from django import forms

from api.config import ConfigManager

class BaseArtifactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()


class ArtifactForm(BaseArtifactForm):
    # New field for artifact URLs
    artifact_url = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'https://example.com/artifact1.pdf',
            'rows': 1,
            'cols': 50,
            'id': 'artifact_url',
        }),
        label="Artifact URL:",
        help_text="Enter URL of the artifact to store with this contract:"
    )
    
    def clean(self):
        """Custom validation logic to ensure at least one field is filled."""
        cleaned_data = super().clean()
        file_path = cleaned_data.get("file_path")
        artifact_urls = cleaned_data.get("artifact_urls")

        if not file_path and not artifact_urls:
            raise forms.ValidationError("Please provide either a File Path or Artifact URLs.")
        
        return cleaned_data