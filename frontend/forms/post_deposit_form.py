from django import forms
from .deposit_form import DepositForm

class PostDepositForm(DepositForm):
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