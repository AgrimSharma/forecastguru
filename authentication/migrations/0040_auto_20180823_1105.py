# -*- coding: utf-8 -*-
# Generated by Django 1.11.14 on 2018-08-23 11:05
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0039_redeempoints'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserNotifications',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_date', models.DateField(auto_now=True)),
                ('forecast', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.ForeCast')),
            ],
            options={
                'verbose_name_plural': 'User Notification',
            },
        ),
        migrations.AlterField(
            model_name='authentication',
            name='last_login',
            field=models.DateField(default=datetime.date(2018, 8, 23)),
        ),
        migrations.AddField(
            model_name='usernotifications',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='authentication.Authentication'),
        ),
    ]