from django.db import models
from django.contrib.auth import get_user_model

class ContractApproval(models.Model):
    contract_idx = models.IntegerField(null=True)
    contract_type = models.CharField(max_length=25)
    contract_release = models.IntegerField(default=0)
    party_code = models.CharField(max_length=20)
    approved = models.BooleanField(default=False)
    approved_dt = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True)
    
    class Meta:
        unique_together = ("contract_type", "contract_release", "contract_idx", "party_code")

    def __str__(self):
        return (
            f"Approval: {self.party_code} for {self.contract_type} "
            f"{self.contract_idx} (release {self.contract_release}) - {'✔' if self.approved else '❌'}"
        )