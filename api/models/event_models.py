from django.db import models

class Event(models.Model):
    event_idx = models.AutoField(primary_key=True) 
    
    # combination of contract_idx and contract_addr should be unique
    contract_idx = models.IntegerField()     
    contract_addr = models.CharField(max_length=255)

    event_type = models.CharField(max_length=50)
    details = models.CharField(max_length=255)
    event_dt = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Contract {self.contract_idx} updated at {self.event_dt}'

    class Meta:
        verbose_name = "Event"
        verbose_name_plural = "Events"