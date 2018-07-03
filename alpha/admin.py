# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import Group, User
from django.contrib import admin
from .models import *
from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy

def approve(modeladmin, request, queryset):
    approved = Approved.objects.get(id=1)
    for obj in queryset:
        obj.approved = approved
        obj.save()


def verified(modeladmin, request, queryset):
    approved = Verified.objects.get(id=1)
    for obj in queryset:
        obj.verified = approved
        obj.save()


class InviteFriendAdmin(admin.ModelAdmin):
    list_display = ['forecast', "user"]
    # pass


class LoginStatusAdmin(admin.ModelAdmin):
    list_display = ['user', "status"]
    # pass


class SubCatInline(admin.TabularInline):
    model = SubCategory


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', "identifier"]
    ordering = ('identifier',)
    inlines = (SubCatInline,)


class PrivateAdmin(admin.ModelAdmin):
    list_display = ['name']


class UserDeviceAdmin(admin.ModelAdmin):
    list_display = ['user', "device_id"]


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


class ApprovedAdmin(admin.ModelAdmin):
    list_display = ['name']


class VerifiedAdmin(admin.ModelAdmin):
    list_display = ['name']


class ForeCastAdmin(admin.ModelAdmin):
    date_hierarchy = 'expire'
    list_display = ['heading', 'category', 'sub_category', 'user', 'expire', 'status']
    search_fields = ['heading']
    list_filter = ("approved", "verified", 'status', 'category', 'private')
    ordering = ('-expire',)
    actions = [approve, verified]


class StatusAdmin(admin.ModelAdmin):
    list_display = ['name']


class BettingAdmin(admin.ModelAdmin):

    list_display = ['get_forecast', "get_forecast_category", "get_forecast_sub_category", 'users', 'bet_for', 'bet_against']
    date_hierarchy = 'forecast__expire'
    search_fields = ['forecast__heading']
    list_filter = ("forecast__category", )
    ordering = ('forecast__expire',)

    def get_forecast(self, obj):
        return obj.forecast.heading

    def get_forecast_category(self, obj):
        return obj.forecast.category

    def get_forecast_sub_category(self, obj):
        return obj.forecast.sub_category


class BannerAdmin(admin.ModelAdmin):
    list_display = ['name', 'image']


class OrderAdmin(admin.ModelAdmin):
    date_hierarchy = 'order_date'
    list_display = ['user', 'amount', 'txnid', 'order_date']
    search_fields = ['user']
    list_filter = ('user', 'amount', 'order_date')


class NotificationUserAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['user', 'subscriber_id']
    search_fields = ['user']


class NotificationAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['user', 'title', "message", "show_firm_url", "status"]
    list_filter = ('status',)

    def show_firm_url(self, obj):
        return '<a href="%s">%s</a>' % (obj.url, obj.url)

    show_firm_url.allow_tags = True

class NotificationAllAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ['title', "message", "url", "status", 'created']
    list_filter = ('status',)


admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(ForeCast, ForeCastAdmin)
admin.site.register(NotificationUser, NotificationUserAdmin)
admin.site.register(SendNotificationAll, NotificationAllAdmin)
admin.site.register(NotificationPanel, NotificationAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Betting, BettingAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Approved, ApprovedAdmin)
admin.site.register(Private, PrivateAdmin)
admin.site.register(Verified, VerifiedAdmin)
admin.site.register(UserDevice, UserDeviceAdmin)
admin.site.register(InviteFriends, InviteFriendAdmin)
admin.site.register(LoginStatus, LoginStatusAdmin)
admin.site.site_title = 'ForeCast Guru'
admin.site.site_header = 'ForeCast Guru'
admin.site.index_title= 'Dashboard'
