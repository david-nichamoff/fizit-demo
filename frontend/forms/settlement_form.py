import logging
from datetime import datetime, timezone

from django import forms

class BaseSettlementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

class SettlementForm(BaseSettlementForm):
    settle_due_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        help_text="Enter the date the settlement will be paid in UTC (Coordinated Universal Time)",
        label="Settlement due date:"
    )

class AdvanceSettlementForm(SettlementForm):
    transact_min_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        help_text="Enter the minimum date & time (inclusive) for transactions in UTC (Coordinated Universal Time)",
        label="Transaction min date:"
    )

    transact_max_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        help_text="Enter the maximum date & time (exclusive) for transactions in UTC (Coordinated Universal Time)",
        label="Transaction max date:"
    )

class SaleSettlementForm(SettlementForm):
    principal_amt = forms.DecimalField(
        required=True,
        initial=0.00,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
        label="Principal amount:",
        help_text="The purchase price of the commodity, for calculation of distribution amounts"
    )

    settle_exp_amt = forms.DecimalField(
        required=True,
        initial=0.00,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
        label="Expected settlement:",
        help_text="The sale price of the commodity, for calculation of distribution amounts"
    )