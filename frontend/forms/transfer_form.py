import logging
from datetime import datetime, timezone

from django import forms

from api.config import ConfigManager

class TransferFundsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.pop("initial", {})
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)
        self.config_manager = ConfigManager()

    from_address = forms.CharField(
        required=False,
        label='From Address:',
        max_length=42,
        widget=forms.TextInput(attrs={'class':'text-input','id':'id_from',  'style':"width: 350px"}),
        help_text="The address to send funds from"
    )

    to_address = forms.CharField(
        required=False,
        label='To Address:',
        max_length=42,
        widget=forms.TextInput(attrs={'class':'text-input','id':'id_to', 'style':"width: 350px"}),
        help_text="The address to send funds to"
    )

    amount = forms.DecimalField(
        required=False,
        label='Amount:',
        min_value=0.0,
        decimal_places=18,
        widget=forms.NumberInput(attrs={'class':'number-input','id':'id_amount'})
    )