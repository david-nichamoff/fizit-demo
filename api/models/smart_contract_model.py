from django.db import models

class SmartContract(models.Model):
    contract_addr = models.CharField(max_length=255, primary_key=True) 
    contract_type = models.CharField(max_length=25) 
    contract_release = models.IntegerField(default=0)
    created_dt = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    expiry_dt = models.DateTimeField(null=True, blank=True)  # Expiry date to be manually set

    def __str__(self):
        return f'Smart Contract {self.contract_addr} (created at {self.created_dt})'

    class Meta:
        verbose_name = "Smart Contract History"
        verbose_name_plural = "Smart Contract History"