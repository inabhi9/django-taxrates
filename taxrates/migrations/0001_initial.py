# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):
    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaxRate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True,
                                        primary_key=True)),
                ('country', models.CharField(max_length=2, db_index=True)),
                ('state', models.CharField(max_length=2, db_index=True)),
                ('zip_code', models.CharField(max_length=20, db_index=True)),
                ('tax_region_name', models.CharField(max_length=254)),
                ('rate', models.FloatField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='taxrate',
            unique_together=set([('country', 'zip_code')]),
        ),
    ]
