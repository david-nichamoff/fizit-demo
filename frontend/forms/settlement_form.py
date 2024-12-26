from django import forms
from api.managers import ConfigManager
from datetime import datetime, timezone

import logging

logger = logging.getLogger(__name__)

class BaseSettlementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})

        super().__init__(*args, **kwargs)

        # Load configuration data once
        self.config = ConfigManager().load_config()


class SettlementForm(BaseSettlementForm):
    # Define static fields
    settle_due_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        help_text="Enter the date the settlement will be paid in UTC (Coordinated Universal Time)",
    )

    transact_min_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        help_text="Enter the minimum date for transactions in UTC (Coordinated Universal Time)",
    )

    transact_max_dt = forms.DateTimeField(
        required=True,
        initial=lambda: datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'datetime-input'}),
        help_text="Enter the maximum date for transactions in UTC (Coordinated Universal Time)",
    )