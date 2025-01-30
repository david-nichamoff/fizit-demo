from django.db import models

class Event(models.Model):
    event_idx = models.AutoField(primary_key=True) 
    contract_idx = models.IntegerField(null=True, blank=True)     
    contract_type = models.CharField(max_length=25)
    network = models.CharField(max_length=50, null=True, blank=True) 
    from_addr = models.CharField(null=True, blank=True, max_length=255)
    to_addr = models.CharField(null=True, blank=True, max_length=255)
    tx_hash = models.CharField(max_length=255, unique=True)
    gas_used = models.BigIntegerField(null=True, blank=True)
    event_type = models.CharField(max_length=50)
    event_dt = models.DateTimeField(auto_now_add=True)
    details = models.CharField(max_length=255)
    status = models.CharField(max_length=50, default="pending")

    def __str__(self):
        return f'Contract {self.contract_idx} updated at {self.event_dt}'

    class Meta:
        verbose_name = "Audit Event"
        verbose_name_plural = "Audit Events"