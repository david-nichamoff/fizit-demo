from django.db import models

class Event(models.Model):
    event_idx = models.AutoField(primary_key=True) 
    
    contract_idx = models.IntegerField(null=True, blank=True)     
    contract_addr = models.CharField(max_length=255)
    network = models.CharField(max_length=50, null=True, blank=True) 
    tx_hash = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default="pending")
    gas_used = models.BigIntegerField(null=True, blank=True)

    event_type = models.CharField(max_length=50)
    details = models.CharField(max_length=255)
    event_dt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Contract {self.contract_idx} updated at {self.event_dt}'

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"