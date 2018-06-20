# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.db import models
from allauth.socialaccount.models import SocialAccount
from django.contrib.auth.models import User



class Approved(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Approved'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Private(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Private'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Verified(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Verified'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Status(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Status'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    identifier = models.IntegerField(default=0)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Category'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class SubCategory(models.Model):
    name = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    image = models.URLField(null=True, blank=True)
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE)
    identifier = models.IntegerField(default=0)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Sub-Category'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class ForeCast(models.Model):
    category = models.ForeignKey(to=Category, on_delete=models.CASCADE)
    sub_category = models.ForeignKey(to=SubCategory, on_delete=models.CASCADE)
    user = models.ForeignKey(to=SocialAccount, on_delete=models.CASCADE)
    heading = models.CharField(max_length=1000)
    start = models.DateTimeField(default=datetime.datetime.now())
    expire = models.DateTimeField()
    status = models.ForeignKey(to=Status, on_delete=models.CASCADE)
    market_fee = models.IntegerField(default=0)
    won = models.CharField(max_length=100, null=True, blank=True)
    created = models.DateField()
    approved = models.ForeignKey(to=Approved, on_delete=models.CASCADE)
    verified = models.ForeignKey(to=Verified, on_delete=models.CASCADE)
    private = models.ForeignKey(to=Private, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-category']
        verbose_name_plural = "FORECAST"

    def __str__(self):
        return "{} : {} : {}".format(self.category, self.sub_category, self.heading)

    def __unicode__(self):
        return "{} : {} : {}".format(self.category, self.sub_category, self.heading)


class Betting(models.Model):
    forecast = models.ForeignKey(to=ForeCast, on_delete=models.CASCADE)
    users = models.ForeignKey(to=SocialAccount, on_delete=models.CASCADE)
    bet_for = models.IntegerField(default=0)
    bet_against = models.IntegerField(default=0)

    class Meta:
        ordering = ['-bet_for']
        verbose_name_plural = "Points In Play"

    def __str__(self):
        return "{} : {}".format(self.forecast, self.users)

    def __unicode__(self):
        return "{} : {}".format(self.forecast, self.users)


class Banner(models.Model):
    name = models.CharField(max_length=100)
    image = models.URLField()

    class Meta:
        ordering = ['-name']
        verbose_name_plural = "Banner"

    def __str__(self):
        return "{}".format(self.name)

    def __unicode__(self):
        return "{}".format(self.name)


class Order(models.Model):
    user = models.ForeignKey(to=SocialAccount, on_delete=models.CASCADE)
    order_date = models.DateField(auto_now=True)
    txnid = models.CharField(max_length=36, primary_key=True)
    amount = models.FloatField(null=True, blank=True, default=0.0)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = "Order"

    def __str__(self):
        return "{} : {} : {}".format(self.user, self.amount,self.txnid)

    def __unicode__(self):
        return "{} : {} : {}".format(self.user, self.amount, self.txnid)


class InviteFriends(models.Model):
    user = models.ForeignKey(to=SocialAccount, on_delete=models.CASCADE)
    forecast = models.ForeignKey(to=ForeCast, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = 'Invite Friends'

    def __str__(self):
        return "{} : {}" .format(self.user.username, self.forecast)

    def __unicode__(self):
        return "{} : {}".format(self.user.username, self.forecast)


class UserDevice(models.Model):
    user = models.ForeignKey(to=SocialAccount, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=10000)
    device_token = models.CharField(max_length=10000)

    class Meta:
        ordering = ['device_id']
        verbose_name_plural = 'User Device'

    def __str__(self):
        return "{} : {}".format(self.user, self.device_id)

    def __unicode__(self):
        return "{} : {}".format(self.user, self.device_id)
