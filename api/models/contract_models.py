from django.db import models

class Contract(models.Model):
    contract_addr = models.CharField(max_length=255, primary_key=True) 
    created_dt = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    expiry_dt = models.DateTimeField()  # Expiry date to be manually set

    def __str__(self):
        return f'Contract {self.contract_addr} (created at {self.created_dt})'

    class Meta:
        verbose_name = "Contract"
        verbose_name_plural = "Contracts"