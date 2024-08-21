from django.db import models

class DataDictionary(models.Model):
    type = models.CharField(max_length=50)
    field_code = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    language_code = models.CharField(max_length=10, default='en')  # Add language_code field

    def __str__(self):
        return f"{self.type} - {self.field_code} ({self.language_code}): {self.display_name}"

    class Meta:
        unique_together = ('type', 'field_code', 'language_code')
        verbose_name_plural = 'Data Dictionary'