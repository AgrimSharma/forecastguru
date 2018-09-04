# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import datetime
from django.db import models


class Authentication(models.Model):
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    facebook_id = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, null=True, blank=True)
    joining_points = models.IntegerField(default=0)
    points_won_public = models.IntegerField(default=0)
    points_won_private = models.IntegerField(default=0)
    successful_forecast = models.IntegerField(default=0)
    unsuccessful_forecast = models.IntegerField(default=0)
    forecast_played = models.IntegerField(default=0)
    market_fee = models.IntegerField(default=0)
    market_fee_paid = models.IntegerField(default=0)
    points_earned = models.IntegerField(default=0)
    forecast_created = models.IntegerField(default=0)
    forecast_participated = models.IntegerField(default=0)
    points_lost_private = models.IntegerField(default=0)
    points_lost_public = models.IntegerField(default=0)
    referral_code = models.CharField(max_length=100)
    referral_status = models.IntegerField(default=0)
    interest_status = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now=True)
    login_count = models.IntegerField(default=0)
    last_login = models.DateField(default=datetime.datetime.now().date())

    class Meta:
        ordering = ['-email']

    def __str__(self):
        return self.email

    def __unicode__(self):
        return self.email


class ReferralCodeRegistered(models.Model):
    referral_code = models.CharField(max_length=10)
    user_joined = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    date_joined = models.DateField(auto_now=True)

    class Meta:
        ordering = ['-date_joined']
        verbose_name_plural = 'Referral Code'

    def __str__(self):
        return self.referral_code

    def __unicode__(self):
        return self.referral_code


class ReferralCodePoints(models.Model):
    points = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Referral Points'

    def __str__(self):
        return self.points

    def __unicode__(self):
        return self.points


class DailyFreePoints(models.Model):
    days = models.IntegerField()
    points = models.IntegerField()

    class Meta:
        ordering = ['days']
        verbose_name_plural = 'Daily Bonus'

    def __str__(self):
        return "{} :{}".format(self.days, self.points)

    def __unicode__(self):
        return "{} :{}".format(self.days, self.points)


class JoiningPoints(models.Model):
    points = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Joining Bonus'

    def __str__(self):
        return self.points

    def __unicode__(self):
        return self.points


class Approved(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Approved'

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


class Private(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Private'

    def __str__(self):
        return self.name

    def __unicode__(self):
        return self.name


class Winning(models.Model):
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ['-name']
        verbose_name_plural = 'Winning'

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
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    heading = models.CharField(max_length=1000)
    status = models.ForeignKey(to=Status, on_delete=models.CASCADE,default=1)
    tags = models.CharField(max_length=1000, null=True, blank=True)
    won = models.ForeignKey(to=Winning, on_delete=models.CASCADE, default=3)
    private = models.ForeignKey(to=Private, on_delete=models.CASCADE, default=1)
    expire = models.DateTimeField()
    created = models.DateField(auto_now=True)

    class Meta:
        ordering = ['-expire']
        verbose_name_plural = "Forecast"

    def __str__(self):
        return "{} : {} : {}".format(self.category, self.sub_category, self.heading)

    def __unicode__(self):
        return "{} : {} : {}".format(self.category, self.sub_category, self.heading)


class Betting(models.Model):
    forecast = models.ForeignKey(to=ForeCast, on_delete=models.CASCADE)
    users = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    bet_for = models.IntegerField(default=0)
    bet_against = models.IntegerField(default=0)

    class Meta:
        ordering = ['-bet_for']
        verbose_name_plural = "Points In Play"

    def __str__(self):
        return "{} : {}".format(self.forecast, self.users)

    def __unicode__(self):
        return "{} : {}".format(self.forecast, self.users)


class UserInterest(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    interest = models.ForeignKey(to=SubCategory, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = "User Interest"

    def __str__(self):
        return "{} : {}".format(self.user, self.interest)

    def __unicode__(self):
        return "{} : {}".format(self.user, self.interest)


class AdvertisementPoints(models.Model):
    points = models.IntegerField()

    class Meta:
        ordering = ['-points']
        verbose_name_plural = "Advertisement Points"

    def __str__(self):
        return "{}".format(self.points)

    def __unicode__(self):
        return "{}".format(self.points)


class MarketFee(models.Model):
    points = models.IntegerField()

    class Meta:
        ordering = ['-points']
        verbose_name_plural = "Market Fee"

    def __str__(self):
        return "{}".format(self.points)

    def __unicode__(self):
        return "{}".format(self.points)


class RateApp(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    rating = models.CharField(max_length=10)
    feedback = models.CharField(max_length=1000)

    class Meta:
        ordering = ['-rating']
        verbose_name_plural = "Application Rating"

    def __str__(self):
        return "{} : {}".format(self.user, self.rating)

    def __unicode__(self):
        return "{} : {}".format(self.user, self.rating)


class ShareForecast(models.Model):
    points = models.IntegerField()

    class Meta:
        ordering = ['-points']
        verbose_name_plural = "Share Forecast Points"

    def __str__(self):
        return "{}".format(self.points)

    def __unicode__(self):
        return "{}".format(self.points)


class HideForecast(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    forecast = models.ForeignKey(to=ForeCast, on_delete=models.CASCADE)
    status = models.IntegerField(default=0)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = "Hidden Forecast"

    def __str__(self):
        return "{} : {} : {}".format(self.user, self.forecast, self.status)

    def __unicode__(self):
        return "{} : {} : {}".format(self.user, self.forecast, self.status)


class ReportAbuseForecast(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    forecast = models.ForeignKey(to=ForeCast, on_delete=models.CASCADE)
    status = models.IntegerField(default=0)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = "Report Abuse Forecast"

    def __str__(self):
        return "{} : {} : {}".format(self.user, self.forecast, self.status)

    def __unicode__(self):
        return "{} : {} : {}".format(self.user, self.forecast, self.status)


class LoginStatus(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    status = models.IntegerField(default=0)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = 'Login Status'

    def __str__(self):
        return "{} : {}" .format(self.user.user.username, self.status)

    def __unicode__(self):
        return "{} : {}".format(self.user.user.username, self.status)


class RedeemPoints(models.Model):
    redeem_points = models.IntegerField()
    redeem_to = models.IntegerField()

    class Meta:
        verbose_name_plural = 'Redeem Points'

    def __str__(self):
        return "{} : {}" .format(self.redeem_points, self.redeem_to)

    def __unicode__(self):
        return "{} : {}".format(self.redeem_points, self.redeem_to)


class UserNotifications(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    forecast = models.ForeignKey(to=ForeCast, on_delete=models.CASCADE)
    notification_date = models.DateField(auto_now=True)

    class Meta:
        verbose_name_plural = 'User Notification'

    def __str__(self):
        return "{} : {} : {}" .format(self.user, self.forecast, self.notification_date)

    def __unicode__(self):
        return "{} : {} : {}".format(self.user, self.forecast, self.notification_date)


class SendNotification(models.Model):
    body = models.CharField(max_length=1000)
    url = models.URLField()
    status = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Send Notification'

    def __str__(self):
        return "{} : {}" .format(self.body, self.url)

    def __unicode__(self):
        return "{} : {}".format(self.body, self.url)


class NotificationUser(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    subscriber_id = models.CharField(max_length=1000)
    created = models.DateField(auto_now=True)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = 'Notification User'

    def __str__(self):
        return "{} : {}".format(self.user.user.username, self.subscriber_id)

    def __unicode__(self):
        return "{} : {}".format(self.user.user.username, self.subscriber_id)


class NotificationPanel(models.Model):
    user = models.ForeignKey(to=Authentication, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, default="Forecast Guru. Predict future.")
    message = models.CharField(max_length=1000)
    url = models.URLField()
    status = models.IntegerField(default=0)
    created = models.DateField(auto_now=True)

    class Meta:
        ordering = ['-user']
        verbose_name_plural = 'Notification Panel'

    def __str__(self):
        return "{} : {}".format(self.user.user.username, self.status)

    def __unicode__(self):
        return "{} : {}".format(self.user.user.username, self.status)


class SendNotificationAll(models.Model):
    title = models.CharField(max_length=1000)
    message = models.CharField(max_length=1000)
    url = models.URLField()
    status = models.IntegerField(default=0)
    created = models.DateField(auto_now=True)

    class Meta:
        ordering = ['-created']
        verbose_name_plural = 'Notification All'

    def __str__(self):
        return "{} : {}".format(self.title, self.status)

    def __unicode__(self):
        return "{} : {}".format(self.title, self.status)
