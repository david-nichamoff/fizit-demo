from django.db import models

class EngageSrc(models.Model):
    src_idx = models.AutoField(primary_key=True)
    src_id = models.IntegerField(unique=True)
    api_key = models.CharField(max_length=100)
    src_code = models.CharField(unique=True, max_length=25)

    def __str__(self):
        return self.src_code

    class Meta:
        verbose_name = "Engage Source"
        verbose_name_plural = "Engage Sources"

class EngageDest(models.Model):
    dest_idx = models.AutoField(primary_key=True)
    dest_id = models.IntegerField(unique=True)
    dest_code = models.CharField(unique=True, max_length=25)

    def __str__(self):
        return self.dest_code

    class Meta:
        verbose_name = "Engage Destination"
        verbose_name_plural = "Engage Destinations"