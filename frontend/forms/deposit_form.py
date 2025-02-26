import logging
from datetime import datetime, timezone, timedelta

from django import forms

from api.config import ConfigManager
from api.utilities.logging import log_info, log_warning, log_error

class BaseDepositForm(forms.Form):
    """Common fields for deposit-related forms"""
    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop("contracts", [])
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()

        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]

        contract_types = sorted(set(contract["contract_type"] for contract in contracts))
        self.fields['contract_type'].choices = [(ct, ct.title()) for ct in contract_types]

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

class FindDepositsForm(BaseDepositForm):
    """Form for searching deposits"""

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

class PostDepositForm(BaseDepositForm):

    def __init__(self, *args, **kwargs):
        settlements = kwargs.pop("settlements", {})
        contracts = kwargs.pop("contracts", [])
        super().__init__(*args, **kwargs)
        self.fields['settle_idx'].choices = []

        self.fields['contract_idx'].choices = [
            (contract['contract_idx'], contract['contract_name']) for contract in contracts
        ]
        log_info(self.logger, f"Contract_idx choice: {self.fields['contract_idx'].choices}")

        contract_types = sorted(set(contract["contract_type"] for contract in contracts))
        self.fields['contract_type'].choices = [(ct, ct.title()) for ct in contract_types]
        log_info(self.logger, f"Contract_type choice: {self.fields['contract_type'].choices}")

        if settlements:
            for key, settlement_list in settlements.items():
                for settlement in settlement_list:
                    self.fields['settle_idx'].choices.append(
                        (settlement["settle_idx"], settlement["settle_due_dt"])
                    )

    """Form for posting a deposit"""
    settle_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'settlement-select', 'id': 'id_settle_idx'}),
        label="Settlement Period:",
        help_text="Select a settlement period for this deposit"
    )

    dispute_reason = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'text-input'}),
        label="Dispute Reason:",
        help_text="Enter the dispute reason if applicable"
    )

    tx_hash = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={'class': 'text-input'}),
        label="Transaction Hash:",
        help_text="Enter the transaction hash for this deposit"
    )

    deposit_dt = forms.DateTimeField(
        required=True,
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        initial=datetime.now(timezone.utc),
        label="Timestamp:",
        help_text="Select the timestamp for this deposit"
    )

    deposit_amt = forms.DecimalField(
        required=True,
        min_value=0.01,
        widget=forms.NumberInput(attrs={'class': 'number-input'}),
        label="Payment Amount:",
        help_text="Enter the deposit amount"
    )