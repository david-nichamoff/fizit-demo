from django.db import models

class ContractAuxiliary(models.Model):
    contract_idx = models.IntegerField(null=True)
    contract_type = models.CharField(max_length=25)
    contract_release = models.IntegerField(default=0)
    logic_natural = models.TextField(blank=True, null=True)  # For storing the natural language translation
    # Add future enhancement fields here, e.g., metadata, notes, etc.
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('contract_idx', 'contract_type', 'contract_release')
        verbose_name = "Contract Auxiliary Data"
        verbose_name_plural = "Contract Auxiliary Data"

    def __str__(self):
        return f"{self.contract_type} #{self.contract_idx} (Release {self.contract_release})"