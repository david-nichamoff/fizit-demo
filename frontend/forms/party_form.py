from django import forms
from api.config import ConfigManager
import logging

logger = logging.getLogger(__name__)

class BasePartyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})

        super().__init__(*args, **kwargs)

        # Load configuration data once
        self.config = ConfigManager().load_config()

        # Populate dynamic fields
        self._populate_dynamic_fields()

    def _populate_dynamic_fields(self):
        """Dynamically populate fields based on configuration."""
        if not self.config:
            log_error(logger, "Failed to load configuration.")
            return

        dynamic_field_choices = {
            "party_code": [item["key"] for item in self.config.get("party_addr", [])],
            "party_type": self.config.get("party_type", []),
        }

        for field, choices in dynamic_field_choices.items():
            if field in self.fields:
                self.fields[field].choices = [(value, value.capitalize()) for value in choices]


class PartyForm(BasePartyForm):
    # Define static fields
    party_code = forms.ChoiceField(
        required=True,
        label="Party code:",
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_party_code"}),
    )
    party_type = forms.ChoiceField(
        required=True,
        label="Party type:",
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_party_type"}),
    )