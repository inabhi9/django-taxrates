from __future__ import absolute_import

from django.contrib import admin

from .models import TaxRate


class TaxRateAdmin(admin.ModelAdmin):
    list_display = ('id', 'country', 'state', 'zip_code', 'rate', 'updated_at')


admin.site.register(TaxRate, TaxRateAdmin)
