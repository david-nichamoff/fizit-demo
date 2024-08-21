from django.db import models

class Configuration(models.Model):
    CONFIG_TYPE_CHOICES = (
        ('string', 'String'),
        ('integer', 'Integer'),
    )

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()  
    config_type = models.CharField(max_length=10, choices=CONFIG_TYPE_CHOICES)

    def __str__(self):
        return f"{self.key} ({self.config_type})"

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
        ordering = ['key']

    def get_value(self):
        if self.config_type == 'integer':
            return int(self.value)
        return self.value