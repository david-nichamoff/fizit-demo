import logging
from django import forms

from api.utilities.logging import log_info, log_error, log_warning

class BaseContractForm(forms.Form):
    """Base form for contracts with shared fields and dynamic configurations."""

    def __init__(self, *args, banks=None, token_list=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)

        # Populate dynamic fields
        self._populate_dynamic_fields(banks, token_list)

    def _populate_dynamic_fields(self, banks, token_list):

        dynamic_field_choices = {
            "funding_method": banks,
            "deposit_method": banks,
            "funding_token_symbol": token_list,
            "deposit_token_symbol": token_list
        }

        for field, choices in dynamic_field_choices.items():
            if field in self.fields:
                if field in ["funding_token_symbol", "deposit_token_symbol"]:  # Token dropdowns
                    self.fields[field].choices = [
                        (value, f"{value.split(':')[1].upper()} ({value.split(':')[0].lower()})")
                        for value in choices
                    ]
                else:
                    self.fields[field].choices = [(value, value) for value in choices]

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

        if cleaned_data.get("funding_instr") == {"dummy": "value"}:
            cleaned_data["funding_instr"] = {}

        if cleaned_data.get("deposit_instr") == {"dummy": "value"}:
            cleaned_data["deposit_instr"] = {}

        funding_token_combo = cleaned_data.get("funding_token_symbol", "")
        deposit_token_combo = cleaned_data.get("deposit_token_symbol", "")

        if ":" in funding_token_combo:
            funding_network, funding_token = funding_token_combo.split(":")
            cleaned_data["funding_token_network"] = funding_network
            cleaned_data["funding_token_symbol"] = funding_token

        if ":" in deposit_token_combo:
            deposit_network, deposit_token = deposit_token_combo.split(":")
            cleaned_data["deposit_token_network"] = deposit_network
            cleaned_data["deposit_token_symbol"] = deposit_token

        return cleaned_data

# ===================================
# Shared Fields for All Contract Forms
# ===================================
class ContractForm(BaseContractForm):
    """Generic contract form with shared fields."""
    contract_name = forms.CharField(
        max_length=50,
        required=True,
        label="Contract name:",
        initial="New Contract"
    )

    funding_instr = forms.JSONField(
        widget=forms.Textarea(attrs={"id": "id_funding_instr"}),
        required=False,
        label="Funding instructions:",
        initial={"dummy": "value"},
        help_text="Fields used to define the account that will be funded"
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
        initial=0.00,
        widget=forms.NumberInput(attrs={"step": "0.01"}),
        label="Service fee amount:",
        help_text="Financing fee, entered as a fixed amount. The total fee can include both pct and fixed amounts"
    )

    transact_logic = forms.JSONField(
        widget=forms.Textarea(attrs={"id": "id_transact_logic"}),
        required=True,
        label="Transaction logic:",
        help_text="The JSON logic used to price each transaction"
    )

    funding_method = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={"id": "id_funding_method"}),
        help_text="The method of payment for advances and residuals"
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

    funding_token_symbol = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={"id": "id_funding_token_symbol"}),
        label="Funding Token:"
    )

# ==============================
# Specific Contract Type Forms
# ==============================

class AdvanceContractForm(ContractForm):
    deposit_instr = forms.JSONField(
        widget=forms.Textarea(attrs={"id": "id_deposit_instr"}),
        required=False,
        label="Deposit instructions:",
        initial={"dummy": "value"},
        help_text="Fields used to define the account that will receive the deposit from the buyer"
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

    deposit_method = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={"id": "id_deposit_method"}),
        help_text="Method of payment for settlement deposits"
    )

    deposit_account = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated via API
        widget=forms.Select(attrs={"id": "id_deposit_account"}),
    )

    deposit_token_symbol = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={"id": "id_deposit_token_symbol"}),
        label="Deposit Token:"
    )

class SaleContractForm(ContractForm):
    """Form specific to Sale Contracts."""
    deposit_instr = forms.JSONField(
        widget=forms.Textarea(attrs={"id": "id_deposit_instr"}),
        required=False,
        label="Deposit instructions:",
        initial={"dummy": "value"},
        help_text="Fields used to define the account that will receive the deposit from the buyer"
    )

    late_fee_pct = forms.DecimalField(
        required=True,
        initial=0.2200,
        widget=forms.NumberInput(attrs={"step": "0.01", "min": "0.0000", "max": "1.0000"}),
        label="Late fee pct:",
        help_text="Entered as an annual rate, assessed daily"
    )

    deposit_method = forms.ChoiceField(
        required=False,
        choices=[],
        widget=forms.Select(attrs={"id": "id_deposit_method"}),
        help_text="Method of payment for settlement deposits"
    )

    deposit_account = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated via API
        widget=forms.Select(attrs={"id": "id_deposit_account"}),
    )

    deposit_token_symbol = forms.ChoiceField(
        required=False,
        choices=[],  # Dynamically populated
        widget=forms.Select(attrs={"id": "id_deposit_token_symbol"}),
    )

class PurchaseContractForm(ContractForm):
    """Form specific to Purchase Contracts."""
    pass