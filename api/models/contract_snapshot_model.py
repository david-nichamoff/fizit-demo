from django.db import models

class ContractSnapshot(models.Model):
    contract_type = models.CharField(max_length=25)
    contract_idx = models.IntegerField()
    contract_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    is_quote = models.BooleanField(default=False)
    transact_logic = models.JSONField()
    last_updated = models.DateTimeField(auto_now=True)  # Auto-update on change

    class Meta:
        unique_together = ("contract_idx", "contract_type")  # ✅ Ensure uniqueness

    def __str__(self):
        return f"Contract {self.contract_idx} - {self.contract_name or 'Unnamed'}"