import logging

from django import forms

from api.config import ConfigManager
from api.registry import RegistryManager
from api.utilities.logging import log_info, log_error, log_warning

class BasePartyForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()
        self.registry_manager = RegistryManager()

        # Populate dynamic fields
        self._populate_dynamic_fields()

    def _populate_dynamic_fields(self):

        dynamic_field_choices = {
            "party_code": self.config_manager.get_party_codes(),
            "party_type": self.registry_manager.get_party_types()
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