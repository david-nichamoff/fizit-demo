import logging
from datetime import datetime, timezone

from django import forms

class BaseTransactionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

class TransactionForm(BaseTransactionForm):
    # Define fields
    contract_idx = forms.ChoiceField(
        required=True,
        choices=[],
        widget=forms.Select(attrs={'class': 'contract-select', 'id':'id_contract_idx'}),
        label="Contract Name:",
        help_text="Select the contract associated with this transaction."
    )

    transact_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        label="Transaction Date:",
        help_text="Enter the date and time of the transaction in UTC (Coordinated Universal Time)."
    )

    transact_logic = forms.JSONField(
        widget=forms.Textarea(attrs={
            "readonly": "readonly",
            "id": "id_transact_logic",
            "style": "width: 100%; height: 75px;"
        }),
        initial={},
        label="Transaction Logic:",
        help_text="The transaction logic JSON for the selected contract (read-only)."
    )

    transact_data = forms.JSONField(
        widget=forms.Textarea(attrs={
            "id": "id_transact_data",
            "style": "width: 100%; height: 75px;"
        }),
        initial={},
        required=True,
        label="Transaction Data:",
        help_text="Update the variables associated with this reading."
    )

    def __init__(self, *args, **kwargs):
        contracts = kwargs.pop('contracts', [])
        super().__init__(*args, **kwargs)

        # Dynamically populate contract choices
        self.fields['contract_idx'].choices = [(contract['contract_idx'], contract['contract_name']) for contract in contracts]