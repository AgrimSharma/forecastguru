# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-06-20 08:28
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('socialaccount', '0004_auto_20180612_1110'),
        ('alpha', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InviteFriends',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
            options={
                'ordering': ['-user'],
                'verbose_name_plural': 'Invite Friends',
            },
        ),
        migrations.CreateModel(
            name='UserDevice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('device_id', models.CharField(max_length=10000)),
                ('device_token', models.CharField(max_length=10000)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialaccount.SocialAccount')),
            ],
            options={
                'ordering': ['device_id'],
                'verbose_name_plural': 'User Device',
            },
        ),
        migrations.CreateModel(
            name='UserLoginStatus',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.IntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialaccount.SocialAccount')),
            ],
            options={
                'ordering': ['user'],
                'verbose_name_plural': 'User Login',
            },
        ),
        migrations.AlterField(
            model_name='forecast',
            name='start',
            field=models.DateTimeField(default=datetime.datetime(2018, 6, 20, 13, 58, 32, 181545)),
        ),
        migrations.AddField(
            model_name='invitefriends',
            name='forecast',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='alpha.ForeCast'),
        ),
        migrations.AddField(
            model_name='invitefriends',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='socialaccount.SocialAccount'),
        ),
    ]
