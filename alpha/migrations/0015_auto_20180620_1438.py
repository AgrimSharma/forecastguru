# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-20 09:08
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('socialaccount', '0004_auto_20180612_1110'),
        ('alpha', '0014_auto_20180620_1430'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialaccount.SocialAccount')),
            ],
            options={
                'ordering': ['-user'],
                'verbose_name_plural': 'Login Status',
            },
        ),
        migrations.RemoveField(
            model_name='invitefriends',
            name='status',
        ),
        migrations.AlterField(
            model_name='forecast',
            name='start',
            field=models.DateTimeField(default=datetime.datetime(2018, 6, 20, 14, 38, 54, 471091)),
        ),
    ]