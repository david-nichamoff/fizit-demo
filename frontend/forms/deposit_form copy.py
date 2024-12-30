from django import forms
from api.managers import ConfigManager
from datetime import datetime, timedelta, timezone

import logging

logger = logging.getLogger(__name__)

class BaseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Load configuration data once for all derived forms
        self.config = ConfigManager().load_config()


class FindDepositsForm(BaseForm):
    # Define fields for filtering deposits
    contract_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id': 'id_contract_idx'}),
        label="Contract Name:",
        help_text="Select contract for deposit filtering"
    )

    start_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={'class': 'datetime-input', 'id': 'id_start_date'}),
        initial=datetime.now(timezone.utc) - timedelta(days=5),
        label="Start Date:",
        help_text="Filter deposits starting from this date"
    )

    end_date = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={'class': 'datetime-input', 'id': 'id_end_date'}),
        initial=datetime.now(timezone.utc),
        label="End Date:",
        help_text="Filter deposits up to this date"
    )

    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop("contracts", [])
        super().__init__(*args, **kwargs)

        # Dynamically populate contract choices
        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]


class PostDepositForm(BaseForm):
    contract_idx = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )

    deposit_dt = forms.DateTimeField(
        widget=forms.HiddenInput(),
        required=True,
        label="Deposit Date:"
    )

    deposit_amt = forms.DecimalField(
        widget=forms.HiddenInput(),
        max_digits=10,
        decimal_places=2,
        required=True,
        label="Deposit Amount:"
    )

    settle_idx = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True,
        label="Settlement Index:"
    )

    dispute_reason = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'dispute-reason-input'}),
        required=False,
        initial="none",
        label="Dispute Reason:",
        help_text="Enter a dispute reason if amount paid is less than amount due"
    )