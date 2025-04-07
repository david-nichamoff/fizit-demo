from django import forms
import logging

class TransferFundsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        networks = kwargs.pop("networks", [])
        tokens_by_network = kwargs.pop("tokens_by_network", {})
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

        # Set token choices for all networks (flattened list)
        token_choices = []
        for network, tokens in tokens_by_network.items():
            for token in tokens:
                token_choices.append((f"{network}:{token}", f"{token} ({network})"))
        self.fields["token_symbol"].choices = token_choices

    token_symbol = forms.ChoiceField(
        required=False,
        label='Token:',
        choices=[],  # Will be populated with ["avalanche:USDT", "fizit:FZT"]
        widget=forms.Select(attrs={'class': 'token-select', 'id': 'id_token_symbol'}),
    )

    from_address = forms.CharField(
        required=True,
        label='From Address:',
        max_length=42,
        widget=forms.TextInput(attrs={'class':'text-input','id':'id_from','style':"width: 350px"})
    )

    to_address = forms.CharField(
        required=True,
        label='To Address:',
        max_length=42,
        widget=forms.TextInput(attrs={'class':'text-input','id':'id_to','style':"width: 350px"})
    )

    amount = forms.DecimalField(
        required=True,
        label='Amount:',
        min_value=0.0,
        decimal_places=18,
        widget=forms.NumberInput(attrs={'class':'number-input','id':'id_amount'})
    )