import logging
from django import forms

from api.utilities.logging import log_info, log_error, log_warning

class BasePartyForm(forms.Form):
    def __init__(self, *args, party_codes=None, party_types=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

        # Populate dynamic fields
        self._populate_dynamic_fields(party_codes, party_types)

    def _populate_dynamic_fields(self, party_codes, party_types):

        dynamic_field_choices = {
            "party_code": party_codes,
            "party_type": party_types
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