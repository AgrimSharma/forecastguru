# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-20 08:38
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('alpha', '0005_auto_20180620_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='forecast',
            name='start',
            field=models.DateTimeField(default=datetime.datetime(2018, 6, 20, 14, 8, 2, 716260)),
        ),
    ]
