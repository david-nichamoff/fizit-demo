import logging

from datetime import datetime, timedelta, timezone
from django import forms

from api.config import ConfigManager

class BaseDepositForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()

class FindDepositsForm(BaseDepositForm):
    contract_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id': 'id_contract_idx'}),
        label="Contract Name:",
        help_text="Select contract for deposit filtering"
    )

    contract_type = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id': 'id_contract_type'}),
        label="Contract Type:",
        help_text="Select contract type for deposit filtering"
    )

    start_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input', 'id': 'id_start_date'}),
        initial=datetime.now(timezone.utc) - timedelta(days=5),
        label="Start Date:",
        help_text="Filter deposits starting from this date"
    )

    end_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local','class': 'datetime-input', 'id': 'id_end_date'}),
        initial=datetime.now(timezone.utc),
        label="End Date:",
        help_text="Filter deposits up to this date"
    )

    # Add hidden field to ensure `find_deposits` is always included in POST data
    find_deposits = forms.CharField(
        required=True,
        widget=forms.HiddenInput(),
        initial="1"
    )

    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop("contracts", [])
        super().__init__(*args, **kwargs)
        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]

        # Set choices dynamically based on available contract types
        contract_types = sorted(set(contract["contract_type"] for contract in contracts))
        self.fields['contract_type'].choices = [(ct, ct.title()) for ct in contract_types]

        # Set contract choices dynamically
        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]