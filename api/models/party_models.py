from django.db import models

class PartyType(models.Model):
    party_type = models.CharField(max_length=10, primary_key=True)

    def __str__(self):
        return self.party_type

    class Meta:
        verbose_name = "Party Type"
        verbose_name_plural = "Party Types"

class PartyCode(models.Model):
    party_code = models.CharField(max_length=20, primary_key=True)
    address = models.CharField(max_length=42)

    def __str__(self):
        return self.party_code

    class Meta:
        verbose_name = "Party Code"
        verbose_name_plural = "Party Codes"