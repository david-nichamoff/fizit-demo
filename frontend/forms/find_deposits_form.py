from django import forms
from datetime import datetime, timedelta, timezone
from .deposit_form import DepositForm

class FindDepositsForm(DepositForm):
    contract_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id': 'id_contract_idx'}),
        label="Contract Name:",
        help_text="Select contract for deposit filtering"
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

    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop("contracts", [])
        super().__init__(*args, **kwargs)
        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]