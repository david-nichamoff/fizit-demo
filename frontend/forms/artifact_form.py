from django import forms
from api.managers import ConfigManager
import logging

logger = logging.getLogger(__name__)

class BaseArtifactForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        super().__init__(*args, **kwargs)

        # Load configuration data once
        self.config = ConfigManager().load_config()


class ArtifactForm(BaseArtifactForm):
    # New field for artifact URLs
    artifact_urls = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'https://example.com/artifact1.pdf',
            'rows': 5,
            'cols': 50,
            'id': 'artifact_urls',
        }),
        label="Artifact URLs:",
        help_text="Enter URLs, one per line."
    )
    
    def clean(self):
        """Custom validation logic to ensure at least one field is filled."""
        cleaned_data = super().clean()
        file_path = cleaned_data.get("file_path")
        artifact_urls = cleaned_data.get("artifact_urls")

        if not file_path and not artifact_urls:
            raise forms.ValidationError("Please provide either a File Path or Artifact URLs.")
        
        return cleaned_data