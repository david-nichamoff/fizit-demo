from django import forms
from api.managers import ConfigManager
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)

class BaseAdvanceForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.pop("initial", {})
        super().__init__(*args, **kwargs)

        # Load configuration data once
        self.config = ConfigManager().load_config()

class AdvanceForm(BaseAdvanceForm):
    # Define fields
    contract_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id': 'id_contract_idx'}),
        label="Contract Name:",
        help_text="Select contract for payment"
    )

    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop("contracts", [])
        super().__init__(*args, **kwargs)

        # Dynamically populate contract choices
        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]