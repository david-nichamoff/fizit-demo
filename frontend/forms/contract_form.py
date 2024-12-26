from django import forms
from api.managers import ConfigManager

import logging

logger = logging.getLogger(__name__)

class BaseContractForm(forms.Form):
    def __init__(self, *args, **kwargs):
        initial = kwargs.get("initial", {})

        super().__init__(*args, **kwargs)

        # Load configuration data once
        self.config = ConfigManager().load_config()

        # Populate dynamic fields
        self._populate_dynamic_fields()

    def _populate_dynamic_fields(self):
        """Dynamically populate fields based on configuration."""
        if not self.config:
            logger.error("Failed to load configuration.")
            return

        dynamic_field_choices = {
            "funding_method": self.config.get("bank", []),
            "deposit_method": self.config.get("bank", []),
            "funding_token_symbol": [item["key"] for item in self.config.get("token_addr", [])],
            "deposit_token_symbol": [item["key"] for item in self.config.get("token_addr", [])],
            "contract_type": self.config.get("contract_type", []),
        }

        for field, choices in dynamic_field_choices.items():
            if field in self.fields:
                self.fields[field].choices = [(value, value.capitalize()) for value in choices]

class ContractForm(BaseContractForm):
    # Define static fields
    contract_name = forms.CharField(
        max_length=255, 
        required=True, 
        label="Contract name:", 
        initial="New Contract"
    )

    contract_type = forms.ChoiceField(
        required=True,
        widget=forms.Select(attrs={"id": "id_contract_type"}),
        label="Contract type:"
    )

    service_fee_pct = forms.DecimalField(
        required=True, 
        initial=0.025,
        widget=forms.NumberInput(attrs={"step": "0.001", "min": "0.0000", "max": "1.0000"}),
        label="Service fee pct:",
        help_text="Financing fee, entered as a percentage of the total value delivered"
    )

    service_fee_amt = forms.DecimalField(
        required=True, 
        initial=5.0000,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.0000"}),
        label="Service fee amt:",
        help_text="Financing fee surcharge, entered as a dollar amount"
    )

    advance_pct = forms.DecimalField(
        required=True, 
        initial=0.8500,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.0000", "max": "1.0000"}),
        label="Advance pct:",
        help_text="The percentage of total value delivered that will be advanced"
    )
    
    late_fee_pct = forms.DecimalField(
        required=True, 
        initial=0.2200,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.0000", "max": "1.0000"}),
        label="Late fee pct:",
        help_text="Entered as an annual rate, assessed daily"
    )
    
    min_threshold_amt = forms.DecimalField(
        required=True, 
        initial=-1000,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
        label="Minimum threshold amt:",
        help_text="Minimum expected value delivered per transaction"
    )
    
    max_threshold_amt = forms.DecimalField(
        required=True, 
        initial=10000,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
        label="Maximum threshold amt:",
        help_text="Maximum expected value delivered per transaction"
    )

    funding_instr = forms.JSONField(
        widget=forms.HiddenInput(attrs={"id": "id_funding_instr"}),
        required=True,
        label="Funding instructions:"
    )

    deposit_instr = forms.JSONField(
        widget=forms.HiddenInput(attrs={"id": "id_deposit_instr"}),
        required=True,
        label="Deposit instructions:"
    )

    transact_logic = forms.JSONField(
        widget=forms.Textarea(attrs={"id": "id_transact_logic"}), 
        required=True,
        label="Transaction logic:",
        help_text="The JSON logic used to price each transaction"
    )

    # Dynamic funding instructions fields
    funding_method = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_funding_method"}),
        help_text="The method of payment for advances and residuals"
    )

    funding_token_symbol = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_funding_token_symbol"}),
    )

    funding_account = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated via API
        widget=forms.Select(attrs={"id": "id_funding_account"}),
    )

    funding_recipient = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated via API
        widget=forms.Select(attrs={"id": "id_funding_recipient"}),
    )

    # Dynamic deposit instructions fields
    deposit_method = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_deposit_method"}),
        help_text="Method of payment for settlement deposits"
    )

    deposit_token_symbol = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_deposit_token_symbol"}),
    )

    deposit_account = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated via API
        widget=forms.Select(attrs={"id": "id_deposit_account"}),
    )

    def clean(self):
        """
        Clean and format decimal fields before posting.
        Fields ending in `_amt` are formatted as "X.XX".
        Fields ending in `_pct` are formatted as "X.XXXX".
        """
        cleaned_data = super().clean()

        # Format fields ending with _amt
        for field_name in self.fields:
            if field_name.endswith('_amt') and field_name in cleaned_data:
                try:
                    cleaned_data[field_name] = f"{float(cleaned_data[field_name]):.2f}"
                except (ValueError, TypeError):
                    raise forms.ValidationError(f"Invalid value for {field_name}.")

        # Format fields ending with _pct
        for field_name in self.fields:
            if field_name.endswith('_pct') and field_name in cleaned_data:
                try:
                    cleaned_data[field_name] = f"{float(cleaned_data[field_name]):.4f}"
                except (ValueError, TypeError):
                    raise forms.ValidationError(f"Invalid value for {field_name}.")

        