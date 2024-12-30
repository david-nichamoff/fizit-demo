from django import forms
from api.managers import ConfigManager

class DepositForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = ConfigManager().load_config()