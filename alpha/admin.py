# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.contrib.auth.models import Group, User
from django.contrib import admin
from .models import *
from django.contrib.admin import AdminSite
from django.utils.translation import ugettext_lazy


# class SourceInline(admin.TabularInline):
#     model = Source


class SubCatInline(admin.TabularInline):
    model = SubCategory


class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']
    inlines = (SubCatInline,)


class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ['name']


class ApprovedAdmin(admin.ModelAdmin):
    list_display = ['name']


class VerifiedAdmin(admin.ModelAdmin):
    list_display = ['name']


class ForeCastAdmin(admin.ModelAdmin):
    # pass
    list_display = ['heading', 'category', 'sub_category', 'user', 'expire', 'status']
    search_fields = ['category', 'sub_category', 'user', 'heading']
    list_filter = ("approved", "verified", 'status', 'category')
    ordering = ('-expire',)


class StatusAdmin(admin.ModelAdmin):
    list_display = ['name']


class BettingAdmin(admin.ModelAdmin):
    list_display = ['forecast', 'users', 'bet_for', 'bet_against']
    change_form_template = 'change_list.html'
    search_fields = ['users', 'forecast']
    list_filter = ("users",)



class BannerAdmin(admin.ModelAdmin):
    list_display = ['name', 'image']


class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'amount', 'txnid', 'order_date']
    search_fields = ['user']
    list_filter = ('user', 'amount', 'order_date')


# admin.site.register(Source, SourceAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(SubCategory, SubCategoryAdmin)
admin.site.register(ForeCast, ForeCastAdmin)
admin.site.register(Status, StatusAdmin)
admin.site.register(Betting, BettingAdmin)
admin.site.register(Banner, BannerAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Approved, ApprovedAdmin)
admin.site.register(Verified, VerifiedAdmin)
admin.site.site_title = 'ForeCast Guru'
admin.site.site_header = 'ForeCast Guru'
admin.site.index_title= 'Dashboard'
