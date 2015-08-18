from django.db import models


class TaxRate(models.Model):
    country = models.CharField(max_length=2, db_index=True)
    state = models.CharField(max_length=2, db_index=True)
    zip_code = models.CharField(max_length=20, db_index=True)
    tax_region_name = models.CharField(max_length=254)
    rate = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('country', 'zip_code')
