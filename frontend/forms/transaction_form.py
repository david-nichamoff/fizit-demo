from django import forms
from api.managers import ConfigManager
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)

class BaseTransactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.pop("initial", {})
        super().__init__(*args, **kwargs)

        # Load configuration data once
        self.config = ConfigManager().load_config()


class TransactionForm(BaseTransactionForm):
    # Define fields
    contract_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id':'id_contract_idx'}),
        label="Contract name:",
        help_text="Select the contract associated with this transaction."
    )

    transact_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        label="Transaction date:",
        help_text="Enter the date and time of the transaction in UTC (Coordinated Universal Time)."
    )

    transact_logic = forms.JSONField(
        widget=forms.Textarea(attrs={
            "readonly": "readonly",
            "id": "id_transact_logic",
            "style": "width: 100%; height: 75px;"
        }),
        initial={},
        label="Transaction logic:",
        help_text="The transaction logic JSON for the selected contract (read-only)."
    )

    transact_data = forms.JSONField(
        widget=forms.Textarea(attrs={
            "id": "id_transact_data",
            "style": "width: 100%; height: 75px;"
        }),
        initial={},
        required=True,
        label="Transaction data:",
        help_text="Update the variables associated with this reading."
    )

    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop('contracts', [])
        super().__init__(*args, **kwargs)

        # Dynamically populate contract choices
        self.fields['contract_idx'].choices = [(contract['contract_idx'], contract['contract_name']) for contract in contracts]