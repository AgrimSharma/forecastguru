# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import json

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, render_to_response
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.db.models import Sum
import datetime
from payu_biz.views import make_transaction
from uuid import uuid4
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
import random
import hashlib, logging
from . import constants
from random import randint, randrange
from . import config
from django.template import RequestContext
from allauth.socialaccount.models import SocialAccount, SocialToken
import hashlib
from django.conf import settings

current = datetime.datetime.now()


def test(request):
    return render(request, 'main.html')


@csrf_exempt
def create_forecast(request):
    if request.method == 'POST':
        # try:
        user = request.POST.get('user', '')
        category = request.POST.get('category', '')
        sub_category = request.POST.get('sub_cat', '')
        heading = request.POST.get('heading', '')
        expire = request.POST.get('expire', '')
        cat = Category.objects.get(id=category)
        sub_cat = SubCategory.objects.get(id=sub_category)

        verified = Verified.objects.get(id=2)
        private_name = request.POST.get("private", '')
        if private_name == "email":
            private = Private.objects.get(id=1)
            approved = Approved.objects.get(id=1)
        else:
            private = Private.objects.get(id=2)
            approved = Approved.objects.get(id=2)
        expires = datetime.datetime.strptime(expire, "%Y-%m-%d %H:%M")

        if expires < current:
            return HttpResponse(json.dumps(dict(status=400, message='end')))
        try:
            users = SocialAccount.objects.get(user=request.user)
        except Exception:
            return HttpResponse(json.dumps(dict(status=400, message='Please Login')))

        status = Status.objects.get(name='In-Progress')
        ForeCast.objects.create(category=cat, sub_category=sub_cat,
                                user=users, heading=heading,
                                expire=datetime.datetime.strptime(expire, "%Y-%m-%d %H:%M"),
                                start=datetime.datetime.now(),
                                approved=approved,
                                status=status, created=current,
                                private=private, verified=verified
                                )
        f = ForeCast.objects.get(category=cat, sub_category=sub_cat,
                                 user=users, heading=heading,
                                 )
        f.user.forecast_created += 1
        f.user.save()
        f.save()
        yes = randrange(1000, 9000, 1000)
        no = randrange(1000, 9000, 1000)
        admin = SocialAccount.objects.get(user__username="admin")
        Betting.objects.create(forecast=f, users=admin, bet_for=yes, bet_against=no)
        if private.name == 'no':
            return HttpResponse(json.dumps(dict(status=200, message='Forecast Created', id=f.id)))
        else:
            return HttpResponse(json.dumps(
                dict(status=200, message='Thank You for creating a private forecast', id=f.id)))  # except Exception:
        #
        #     return HttpResponse(json.dumps(dict(status=400, message='Try again later')))

    else:
        try:
            user = request.user
            profile = SocialAccount.objects.get(user=user)
            category = Category.objects.all().order_by('identifier')
            return render(request, 'create_forecast.html', {'category': category,
                                                            "current": datetime.datetime.now().strftime(
                                                                "%Y-%m-%d %H:%M"),
                                                            "user": "Guest" if request.user.is_anonymous() else request.user.username,
                                                            "heading": "Create Forecast",
                                                            "title": "Create Forecast",
                                                            })
        except Exception:
            return render(request, 'create_forecast_nl.html', {"heading": "Create Forecast",
                                                               "title": "Create Forecast",
                                                               "user": "Guest" if request.user.is_anonymous() else request.user.username, })


def closing_soon(request):
    forecast = ForeCast.objects.filter(start__lte=current, approved__name="yes", status__name='Closing Soon').order_by(
        "expire")
    return render(request, 'closing_soon.html', {"forecast": forecast})


def live_forecast(request):
    data = []
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)
        forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no',
                                                status__name='In-Progress').order_by("expire")
        for f in forecast_live:
            date = current.date()

            bet_start = f.expire.date()
            if date == bet_start:
                start = f.expire + datetime.timedelta(hours=5, minutes=30)
                start = start.time()
                today = 'yes'
            else:
                start = f.expire

                today = "no"
            betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
            try:
                total_wagered = betting_against + betting_for
                bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_for_user = Betting.objects.filter(forecast=f, users=profile).aggregate(bet_for=Sum('bet_for'))[
                    'bet_for']
                bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                bet_against_user = \
                    Betting.objects.filter(forecast=f, users=profile).aggregate(bet_against=Sum('bet_against'))[
                        'bet_against']
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)

                total = Betting.objects.filter(forecast=f).count()
            except Exception:
                total_wagered = 0
                bet_against_user = 0
                bet_for_user = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = Betting.objects.filter(forecast=f).count()
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=f,
                             total=total, start=start, total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, bet_for=bet_for,
                             bet_against=bet_against,
                             bet_for_user=bet_for_user if bet_for_user else 0,
                             bet_against_user=bet_against_user if bet_against_user else 0))
    except Exception:
        forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no',
                                                status__name='In-Progress').order_by("expire")
        for f in forecast_live:
            date = current.date()

            bet_start = (f.expire).date()
            if date == bet_start:
                start = f.expire + datetime.timedelta(hours=5, minutes=30)
                print(start)
                start = start.time()
                today = 'yes'
            else:
                start = f.expire

                today = "no"
            betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
            try:
                total_wagered = betting_against + betting_for
                bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)

                total = Betting.objects.filter(forecast=f).count()
            except Exception:
                total_wagered = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = Betting.objects.filter(forecast=f).count()
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=f,
                             total=total, start=start, total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, bet_for=bet_for,
                             bet_against=bet_against,
                             bet_for_user=0,
                             bet_against_user=0))

    return render(request, 'live_forecast.html', {"live": data,
                                                  "heading": "Forecasts",
                                                  "title": "Forecasts",
                                                  "user": "Guest" if request.user.is_anonymous() else request.user.username})


def forecast_result(request):
    data = []
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)

        forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no',
                                                status__name='Result Declared').order_by("-expire")
        for f in forecast_live:
            date = current.date()
            bet_start = f.expire.date()
            if date == bet_start:
                start = f.expire + datetime.timedelta(hours=5, minutes=30)
                start = start.time()
                today = 'yes'
            else:
                start = f.expire
                today = 'no'
            betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

            try:
                bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_for_user = Betting.objects.filter(forecast=f, users=profile).aggregate(bet_for=Sum('bet_for'))[
                    'bet_for']
                bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                bet_against_user = \
                Betting.objects.filter(forecast=f, users=profile).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                total_wagered = betting_against + betting_for
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)
                total = bet_against + bet_for
            except Exception:
                total_wagered = 0
                bet_against_user = 0
                bet_for_user = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = 0
            status = "yes" if f.won == "yes" else "no"
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                             forecast=f, total=total, start=start,
                             total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',
                             ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                             bet_for=bet_for,
                             bet_for_user=bet_for_user if bet_for_user else 0,
                             bet_against_user=bet_against_user if bet_against_user else 0,
                             ))
    except Exception:
        forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no',
                                                status__name='Result Declared').order_by(
            "-expire")
        for f in forecast_live:
            date = current.date()
            bet_start = (f.expire).date()
            if date == bet_start:
                start = f.expire + datetime.timedelta(hours=5, minutes=30)
                start = start.time()
                today = 'yes'
            else:
                start = f.expire
                today = 'no'
            betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

            try:
                bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                total_wagered = betting_against + betting_for
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)
                total = bet_against + bet_for
            except Exception:
                total_wagered = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = 0
            status = "yes" if f.won == "yes" else "no"
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                             forecast=f, total=total, start=start,
                             total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',
                             ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                             bet_for=bet_for,
                             bet_for_user=0,
                             bet_against_user=0
                             ))

    return render(request, 'forecast_result.html', {"live": data,
                                                    "user": "Guest" if request.user.is_anonymous() else request.user.username,
                                                    "heading": "Results",
                                                    "title": "Forecast Result",
                                                    })


def result_not_declared(request):
    forecast_result = ForeCast.objects.filter(approved__name="yes", private__name='no', status__name='Closed',
                                              verified__name='no').order_by("-expire")
    data = []
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)

        for f in forecast_result:
            date = current.date()
            bet_start = (f.expire).date()
            if date == bet_start:
                start = f.expire + datetime.timedelta(hours=5, minutes=30)
                start = start.time()
                today = 'yes'
            else:
                start = f.expire
                today = 'no'
            betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

            try:
                bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_for_user = Betting.objects.filter(forecast=f, users=profile).aggregate(bet_for=Sum('bet_for'))[
                    'bet_for']
                bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                bet_against_user = \
                Betting.objects.filter(forecast=f, users=profile).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                total_wagered = betting_against + betting_for
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)
                total = bet_against + bet_for
            except Exception:
                total_wagered = 0
                bet_against_user = 0
                bet_for_user = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = 0
            status = "yes" if f.won == "yes" else "no"
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                             forecast=f, total=total, start=start,
                             total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',
                             ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                             bet_for=bet_for, bet_against_user=bet_against_user if bet_against_user else 0,
                             bet_for_user=bet_for_user if bet_for_user else 0))
    except Exception:
        for f in forecast_result:
            date = current.date()
            bet_start = (f.expire).date()
            if date == bet_start:
                start = f.expire + datetime.timedelta(hours=5, minutes=30)
                start = start.time()
                today = 'yes'
            else:
                start = f.expire
                today = 'no'
            betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

            try:
                bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                total_wagered = betting_against + betting_for
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)
                total = bet_against + bet_for
            except Exception:
                total_wagered = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = 0
            status = "yes" if f.won == "yes" else "no"
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                             forecast=f, total=total, start=start,
                             total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',
                             ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                             bet_for=bet_for, bet_for_user=0, bet_againet_user=0))
    return render(request, 'forecast_result_pending_no.html', {
        "result": data,
        "user": "Guest" if request.user.is_anonymous() else request.user.username,
        "heading": "Results",
        "title": "Forecast Result",
    })


def get_ratio(bet_for, bet_against, total, status):
    ratio = 0
    if bet_against == 0 and bet_for == 0:
        ratio = "NA"
    elif bet_for == bet_against:
        ratio = 2
    elif status == 'yes':
        try:
            if bet_against > 0:
                ratio = 1 + round((bet_against / bet_for), 2)
            else:
                ratio = 0
        except Exception:
            ratio = 1
    elif status == "no":
        try:
            if bet_for > 0:
                ratio = 1 + round((bet_for / bet_against), 2)
            else:
                ratio = 0
        except Exception:
            ratio = 1
    return ratio


def profile(request):
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)
    except Exception:
        user = request.user
        return render(request, 'user_profile_nl.html', {
            "users": user.username,

        })
    date_joined = datetime.datetime.strftime(profile.date_joined, '%b %d, %Y')
    try:
        bet_for = \
        Betting.objects.filter(users=profile, forecast__status__name="In-Progress").aggregate(bet_for=Sum('bet_for'))[
            'bet_for']
    except Exception:
        bet_for = 0
    try:
        bet_for_close = \
        Betting.objects.filter(users=profile, forecast__status__name="Closed").aggregate(bet_for=Sum('bet_for'))[
            'bet_for']
    except Exception:
        bet_for_close = 0
    try:
        bet_against = Betting.objects.filter(users=profile, forecast__status__name="In-Progress").aggregate(
            bet_against=Sum('bet_against'))['bet_against']
    except Exception:
        bet_against = 0
    try:
        bet_against_close = Betting.objects.filter(users=profile, forecast__status__name="Closed").aggregate(
            bet_against=Sum('bet_against'))['bet_against']
    except Exception:
        bet_against_close = 0

    if bet_against == None:
        bet_against = 0
    if bet_for == None:
        bet_for = 0
    if bet_for_close == None:
        bet_for_close = 0
    if bet_against_close == None:
        bet_against_close = 0

    point = bet_against + bet_for + bet_for_close + bet_against_close

    total = profile.fg_points_free + profile.market_fee + profile.fg_points_won + profile.fg_points_bought - profile.fg_points_lost - profile.market_fee_paid - point
    profile.fg_points_total = total
    totals = profile.successful_forecast + profile.unsuccessful_forecast
    try:
        suc_per = (profile.successful_forecast / totals) * 100
        unsuc_per = (profile.unsuccessful_forecast / totals) * 100
        if suc_per == 0:
            suc_per = 0
        if unsuc_per == 0:
            unsuc_per = 0
    except Exception:
        suc_per = 0
        unsuc_per = 0
    if profile.fg_points_total == 0:
        profile.fg_points_total = profile.fg_points_free + profile.fg_points_bought + profile.fg_points_won - \
                                  profile.fg_points_lost + profile.market_fee - profile.market_fee_paid
    profile.save()
    fore = ForeCast.objects.filter(user=profile).count()
    return render(request, 'user_profile.html', {"profile": profile,
                                                 "date_joined": date_joined,
                                                 "success": int(suc_per),
                                                 "unsuccess": int(unsuc_per),
                                                 "user": request.user.username,
                                                 "point": point,
                                                 "created": fore,
                                                 "total": profile.market_fee + profile.fg_points_won + profile.fg_points_bought - profile.fg_points_lost - profile.market_fee_paid - point,
                                                 "status": predict_status(profile, suc_per),
                                                 "balance": profile.fg_points_total
                                                 })


def predict_status(profile, suc_per):
    if 0 <= profile.forecast_created < 10 and 0 <= suc_per < 50:
        status = "Beginner"
        return status
    elif 10 <= profile.forecast_created < 30 and 50 <= suc_per < 70:
        status = "Expert"
        return status
    elif 30 <= profile.forecast_created < 50 and 70 <= suc_per < 90:
        status = "INFLUENCER"
        return status
    elif profile.forecast_created >= 50 and suc_per >= 90:
        status = "Guru"
        return status
    else:
        status = "Beginner"
        return status


def betting(request, userid):
    forecast = ForeCast.objects.get(id=userid)
    try:
        if request.user.is_anonymous():
            users = "Guest"
        else:
            users = request.user.username
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        betting_sum = Betting.objects.filter(forecast=forecast).aggregate(
            bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
        try:
            total_wagered = betting_sum['bet_for'] + betting_sum['bet_against']
        except Exception:
            total_wagered = 0
        expires = forecast.expire + datetime.timedelta(hours=5, minutes=30)
        end_date = datetime.datetime.strftime(expires, '%b %d, %Y')
        end_time = datetime.datetime.strftime(expires, '%H:%M')
        try:
            percent = round((betting_for / (betting_for + betting_against)) * 100, 2)
        except Exception:
            percent = 0

        if forecast.status.name == 'In-Progress':
            status = 'Currently Live'
        elif forecast.status.name == 'Closed':
            status = 'Currently Closed'
        else:
            status = 'Result Declared'
        try:
            success = SocialAccount.objects.get(user__username=request.user)
            success = success.successful_forecast
        except Exception:
            success = 0
        approved = "yes" if forecast.approved.name == 'yes' and forecast.status.name == 'In-Progress' else 'no'
        return render(request, 'betting.html', {'forecast': forecast, 'betting': betting,
                                                'bet_for': betting_sum['bet_for'] if betting_sum['bet_for'] else 0,
                                                'against': betting_sum['bet_against'] if betting_sum[
                                                    'bet_against'] else 0,
                                                'total': total_wagered if total_wagered else 0,
                                                "end_date": end_date, "end_time": end_time,
                                                'status': status, "percent": percent,
                                                "success": success,
                                                "users": forecast.user.user.username,
                                                "sums": betting_sum['bet_for'] + betting_sum['bet_against'],
                                                "approved": approved,
                                                "user": users,
                                                "heading": "Forecast Details",
                                                "title": "Forecast Details",
                                                })
    except Exception:
        return render(request, 'betting.html', {'forecast': forecast, "user": request.user.username,
                                                "heading": "Forecast Details",
                                                "title": "Forecast Details",
                                                })


@csrf_exempt
def bet_post(request):
    if request.method == 'POST':
        try:
            user = request.user
            account = SocialAccount.objects.get(user=user)
        except Exception:
            return HttpResponse(json.dumps(dict(message='login')))
        vote = request.POST.get('vote')
        points = int(request.POST.get('points'))
        if int(points) % 1000 != 0:
            return HttpResponse(json.dumps(dict(message='Points should be multiple of 1000')))
        forecast = request.POST.get('forecast')
        forecasts = ForeCast.objects.get(id=forecast)
        if account.fg_points_total - points > 0:
            try:
                b = Betting.objects.get(forecast=forecasts, users=account)
                if vote == 'email':
                    # if b.bet_for < points:
                    b.bet_for += points
                    b.users.fg_points_total = b.users.fg_points_total - points
                    b.users.save()
                    b.save()
                    # else:
                    #     return HttpResponse(json.dumps(
                    #         dict(message="FG point for forecast should be greater than previous {}".format(b.bet_for))))
                else:
                    # if b.bet_against < points:
                    b.bet_against += points
                    b.users.fg_points_total = b.users.fg_points_total - points
                    b.users.save()
                    b.save()
                    # else:
                    #     return HttpResponse(json.dumps(
                    #         dict(message="FG point for forecast should be greater than previous {}".format(
                    #             b.bet_against))))
            except Exception:
                if vote == 'email':
                    b = Betting.objects.create(forecast=forecasts, users=account, bet_for=points, bet_against=0)
                    b.users.fg_points_total = b.users.fg_points_total - points
                    b.users.forecast_participated += 1
                    b.users.save()
                    b.save()
                else:
                    b = Betting.objects.create(forecast=forecasts, users=account, bet_for=0, bet_against=points)
                    b.users.fg_points_total = b.users.fg_points_total - points
                    b.users.forecast_participated += 1
                    b.users.save()
                    b.save()
            return HttpResponse(json.dumps(dict(message='success')))
        else:
            return HttpResponse(json.dumps(dict(message='balance')))
    else:
        return HttpResponse(json.dumps(dict(message='Please use POST')))


# def deduct_points(account, points):
#     if account.fg_points_bought > 0 and account.fg_points_bought > points:
#         account.fg_points_bought -= points
#     elif account.fg_points_won > 0 and account.fg_points_won> points:
#         account.fg_points_won -= points
#     elif account.market_fee > 0 and account.market_fee > points:
#         account.market_fee -= account.market_fee - points
#     elif account.fg_points_free > 0 and account.fg_points_free > points:
#         account.fg_points_free -= points
#
#     account.fg_points_total = account.fg_points_won + account.fg_points_bought + account.market_fee + account.fg_points_free
#     account.save()


def allocate_points(request):
    forecast = ForeCast.objects.filter(status__name='Closed', verified__name="yes")
    status = Status.objects.get(name='Result Declared')
    for f in forecast:
        f.status = status

        f.status.save()
        f.save()
        try:
            betting_sum = Betting.objects.filter(forecast=f).aggregate(
                bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
            bet_for = betting_sum['bet_for']
            bet_against = betting_sum['bet_against']
            total = (bet_against + bet_for) * 0.10

        except Exception:
            bet_for = 0
            bet_against = 0
            total = 0
        market_fee = total
        if f.won == "yes" and market_fee > bet_against:
            f.user.market_fee = bet_against * 0.05
            f.user.save()
            f.save()
        elif f.won == "no" and market_fee > bet_for:
            f.user.market_fee = bet_for * 0.05
            f.user.save()
            f.save()
        else:
            if bet_for == bet_against:
                if f.won == "yes":
                    ratio = 1
                    forecast_data(f, ratio, total, "yes", bet_for)
                else:
                    ratio = 1
                    forecast_data(f, ratio, total, "no", bet_against)
            elif bet_for > 0 and bet_against == 0 and f.won == 'yes':
                ratio = 1
                forecast_data(f, ratio, total, "yes", bet_for)
            elif bet_against > 0 and bet_for > 0 and f.won == 'yes':
                ratio = round(bet_against / bet_for, 2)
                forecast_data(f, ratio, total, "yes", bet_for)
            elif f.won == 'no' and bet_against == 0 and bet_for > 0:
                ratio = 0
                forecast_data(f, ratio, total, "no", bet_against)

            elif bet_against > 0 and bet_for == 0 and f.won == 'no':
                ratio = 1
                forecast_data(f, ratio, total, "no", bet_against)
            elif bet_for > 0 and f.won == 'no' and bet_against > 0:
                ratio = round(bet_for / bet_against, 2)
                forecast_data(f, ratio, total, "no", bet_against)
            elif f.won == 'yes' and bet_for > 0 and bet_against == 0:
                ratio = 0
                forecast_data(f, ratio, total, "yes", bet_for)
            elif bet_for == 0 and bet_against == 0:
                f.won = "No Result."
                f.save()
            f.user.market_fee += (bet_against + bet_for) * 0.05
            f.user.save()
            f.save()
            total -= total * 0.10
    return HttpResponse("success")


def forecast_data(forecast, ratio, total, status, total_bets):
    betting = Betting.objects.filter(forecast=forecast)
    ratio += 1
    for b in betting:
        print(b.users.user.username)
        bet_for = b.bet_for
        bet_against = b.bet_against
        if bet_for == 0 and bet_against == 0:
            b.forecast.won = "NA"
            b.forecast.save()
            b.save()
        elif status == "yes":
            if bet_for > 0 and bet_against == 0:
                # bets = (bet_for/total_bets) * total
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.successful_forecast += 1
                b.users.save()
                b.save()
            elif bet_for > 0 and bet_against > 0:
                # bets = (bet_for / total_bets) * total
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.successful_forecast += 1
                b.users.fg_points_lost += bet_against
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()
            elif bet_against == bet_for:
                # bets = (bet_for / total_bets) * total
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.successful_forecast += 1
                b.users.save()
                b.save()
            elif bet_against > 0 and bet_for == 0:
                b.users.fg_points_lost += bet_against
                # b.users.market_fee_paid += bet_against * 0.10
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()

        elif status == "no":
            if bet_against > 0 and bet_for == 0:
                # bets = (bet_against / total_bets) * total
                b.users.fg_points_won += bet_against * ratio
                b.users.market_fee_paid += bet_against * 0.10
                b.users.successful_forecast += 1
                b.users.save()
                b.save()
            elif bet_for > 0 and bet_against > 0:
                # bets = (bet_against / total_bets) * total
                b.users.fg_points_won += bet_against * ratio
                b.users.market_fee_paid += bet_against * 0.10
                b.users.fg_points_lost += bet_for
                b.users.successful_forecast += 1
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()
            elif bet_against == bet_for:
                # bets = (bet_against / total_bets) * total
                b.users.fg_points_won += bet_against * ratio
                b.users.market_fee_paid += bet_against * 0.10
                b.users.fg_points_lost += bet_for
                b.users.successful_forecast += 1
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()
            elif bet_for > 0 and bet_against == 0:
                b.users.fg_points_lost += bet_for
                # b.users.market_fee_paid += bet_for * 0.10
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()


@csrf_exempt
def payments(request):
    if request.method == "POST":
        data = {}
        user = request.user
        so = SocialAccount.objects.get(user=user)
        email = so.user.email
        amount = request.POST.get("button1")

        txnid = get_transaction_id()
        hash_ = generate_hash(request, txnid, amount)
        hash_string = get_hash_string(request, txnid, amount)
        data["action"] = constants.PAYMENT_URL_LIVE
        data["amount"] = float(constants.PAID_FEE_AMOUNT[amount])
        data["productinfo"] = constants.PAID_FEE_PRODUCT_INFO[amount]
        data["key"] = config.KEY
        data["txnid"] = txnid
        data["hash"] = hash_
        data["hash_string"] = hash_string
        data["firstname"] = request.user.username
        data["email"] = str(email)
        data["phone"] = ""
        data["service_provider"] = constants.SERVICE_PROVIDER
        data["furl"] = request.build_absolute_uri("/payubiz-failure/")
        data["surl"] = request.build_absolute_uri("/payubiz-success/")

        return render(request, "payment_form.html", data)


# generate the hash
def generate_hash(request, txnid, amount):
    try:
        # get keys and SALT from dashboard once account is created.
        # hashSequence = "key|txnid|amount|productinfo|firstname|email|udf1|udf2|udf3|udf4|udf5|udf6|udf7|udf8|udf9|udf10"
        hash_string = get_hash_string(request, txnid, amount)
        generated_hash = hashlib.sha512(hash_string.encode('utf-8')).hexdigest().lower()
        return generated_hash
    except Exception as e:
        # log the error here.
        # logging.getLogger("error_logger").error(traceback.format_exc())
        return None


# create hash string using all the fields
def get_hash_string(request, txnid, amount):
    user = request.user
    so = SocialAccount.objects.get(user=user)
    name = so.user.username

    email = so.user.email
    hash_string = config.KEY + "|" + txnid + "|" + str(float(constants.PAID_FEE_AMOUNT[amount])) + "|" + \
                  constants.PAID_FEE_PRODUCT_INFO[amount] + "|" + name + "|" + email + "|||||||||||" + config.SALT
    print(hash_string)
    return hash_string


# generate a random transaction Id.
def get_transaction_id():
    hash_object = hashlib.sha256(str(randint(0, 9999)).encode("utf-8"))
    # take approprite length
    txnid = hash_object.hexdigest().lower()[0:32]
    return txnid


# no csrf token require to go to Success page.
# This page displays the success/confirmation message to user indicating the completion of transaction.
@csrf_exempt
def payment_success(request):
    data = {}
    return render(request, "success.html", data)


# no csrf token require to go to Failure page. This page displays the message and reason of failure.
@csrf_exempt
def payment_failure(request):
    data = {}
    return render(request, "failure.html", data)


@csrf_exempt
def home(request):
    if request.method == "POST":
        amount = request.POST.get('button1', 0)
        account = SocialAccount.objects.get(user=request.user)
        """ DO your stuffs here and create a dictionary (key,value pair) """
        cleaned_data = {
            "key": "r1dykxR5", "salt": "B27ayY3tln",
            'txnid': uuid4(), 'amount': int(amount), 'productinfo': "sample_produ",
            'firstname': account.user.username, 'email': "agrim.sharma@sirez.com", 'udf1': '',
            'udf2': '', 'udf3': '', 'udf4': '', 'udf5': '', 'udf6': '', 'udf7': '',
            'udf8': '', 'udf9': '', 'udf10': '', 'phone': "8800673006"
        }
        """ Payment gate calling with provided data dict """
        return HttpResponse(make_transaction(cleaned_data))


def payment(request):
    try:

        account = SocialAccount.objects.get(user=request.user)

        return render(request, "payumoney.html", {"heading": "Payments",
                                                  "title": "Payments",
                                                  "user": "Guest" if request.user.is_anonymous() else request.user.username})
    except Exception:
        return render(request, "payumoney_nl.html", {"heading": "Payments",
                                                     "title": "Payments", })


@csrf_exempt
def payu_success(request):
    """ we are in the payu success mode"""
    account = SocialAccount.objects.get(user=request.user)

    data = json.loads(json.dumps(request.POST))
    account.fg_points_bought += int(constants.PAID_FEE_TOKENS[str(int(float(data['amount'])))])
    account.fg_points_total += account.fg_points_bought
    account.save()
    Order.objects.create(user=account, order_date=current, txnid=data['txnid'], amount=int(float(data['amount'])))
    return HttpResponseRedirect("/user_profile/")


@csrf_exempt
def payu_failure(request):
    """ We are in payu failure mode"""
    return HttpResponseRedirect("/user_profile/")


@csrf_exempt
def payu_cancel(request):
    """ We are in the Payu cancel mode"""
    return HttpResponseRedirect("/user_profile/")


def category(request):
    category = Category.objects.all().order_by('identifier')
    print(category.count())
    data = []
    for c in category:
        image = c.subcategory_set.get(name='Others').image

        data.append(dict(name=c.name, id=c.id, image=image))
        print(data)
    return render(request, 'category.html', {'category': data,
                                             "heading": "Categories",
                                             "title": "Categories",
                                             "user": "Guest" if request.user.is_anonymous() else request.user.username})


def category_search(request, userid):
    category_id = Category.objects.get(id=userid)
    sub = SubCategory.objects.filter(category=category_id).order_by('identifier')
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)
        if len(forecast_live_view(category_id, profile)) == 0:
            return render(request, 'my_friend_no.html',{
                              "heading": category_id.name, 
                              "title": category_id.name,
                              "user": "Guest" if request.user.is_anonymous() else request.user.username
                          })

        else:
            return render(request, 'category_search.html',
                          {
                              "live": forecast_live_view(category_id, profile),
                              "heading": category_id.name, "sub": sub,
                              "title": category_id.name, 'category_id': category_id.id,
                              "user": "Guest" if request.user.is_anonymous() else request.user.username
                          })

    except Exception:

        return render(request, 'category_search.html',
                      {
                          "live": forecast_live_view_bt(category_id),
                          "heading": category_id.name, "sub": sub,
                          "title": category_id.name, 'category_id': category_id.id,
                          "user": "Guest" if request.user.is_anonymous() else request.user.username
                      })


def sub_category_data(request, userid):
    subcategory = SubCategory.objects.get(id=userid)
    sub = SubCategory.objects.filter(category=subcategory.category).order_by('identifier')
    category = Category.objects.get(id=subcategory.category.id)
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)
        if len(forecast_live_view_sub(subcategory, profile)) == 0:
            return render(request, "my_friend_no.html",{
                              "heading": subcategory.name,
                              "title": subcategory.name,
                              "user": "Guest" if request.user.is_anonymous() else request.user.username
                          })
        else:
            return render(request, 'category_search.html',
                          {
                              "live": forecast_live_view_sub(subcategory, profile),
                              "heading": subcategory.name, "sub": sub,
                              "title": subcategory.name, "category_id": category.id,
                              "user": "Guest" if request.user.is_anonymous() else request.user.username
                          })

    except Exception:

        return render(request, 'category_search.html',
                      {
                          "live": forecast_live_view_bt_sub(subcategory),
                          "heading": subcategory.name, "sub": sub,
                          "title": subcategory.name, "category_id": category.id,
                          "user": "Guest" if request.user.is_anonymous() else request.user.username
                      })


def my_forecast(request):
    try:
        user = request.user.id
        users = User.objects.get(id=user)
        account = SocialAccount.objects.get(user=users)
        forecast_live = Betting.objects.filter(forecast__approved__name="yes", forecast__status__name='In-Progress',
                                               users=account, forecast__private__name='no').order_by("forecast__expire")
        forecast_result = Betting.objects.filter(forecast__approved__name="yes",
                                                 forecast__status__name='Result Declared', users=account,
                                                 forecast__private__name='no').order_by("forecast__expire")
        forecast_approval = ForeCast.objects.filter(approved__name="no", user=account, private__name='no').order_by(
            "expire")
        forecast_no_bet = ForeCast.objects.filter(approved__name="yes", user=account, private__name='no').order_by(
            "expire")
        not_bet = [f for f in forecast_no_bet if f.betting_set.all().count() == 0]
        if forecast_live.count() == 0 and forecast_result.count() == 0 and forecast_approval.count() == 0 and forecast_no_bet.count() == 0:
            return render(request, 'my_friend_no.html', {"heading": "My Forecast",
                                                         "title": "My Forecast",
                                                         "user": "Guest" if request.user.is_anonymous() else request.user.username})
        else:
            return render(request, 'my_friend.html', {"live": live_forecast_data(forecast_live, account),
                                                      "result": forecast_result_data(forecast_result, account),
                                                      "approval": forecast_approval,
                                                      "forecast": live_forecast_data_bet(not_bet, account),
                                                      "heading": "My Forecast",
                                                      "title": "My Forecast",
                                                      "user": "Guest" if request.user.is_anonymous() else request.user.username})

    except Exception:
        return render(request, 'my_friend_nl.html', {"heading": "My Forecast",
                                                     "title": "My Forecast",
                                                     "user": "Guest" if request.user.is_anonymous() else request.user.username})


def logout_view(request):
    logout(request)

    return HttpResponseRedirect("/home/")


def blank_page(request):
    return render(request, 'test.html', {})


@csrf_exempt
def search_result(request):
    if request.method == "POST":

        query = request.POST.get('point', '')
        if query == "":
            return render(request, "search_data_nf.html", {"data": "No result found", "heading": "Search Forecast",
                                                           "title": "Search Forecast",
                                                           "user": "Guest" if request.user.is_anonymous() else request.user.username})
        else:
            data = []

            forecast_live = ForeCast.objects.filter(heading__icontains=query, private__name='no', approved__name="yes",
                                                    status__name='In-Progress').order_by(
                "-expire")
            if len(forecast_live) == 0:
                return render(request, "search_data_nf.html", {"data": "No result found", "heading": "Search Forecast",
                                                               "title": "Search Forecast",
                                                               "user": "Guest" if request.user.is_anonymous() else request.user.username})
            else:
                for f in forecast_live:
                    date = current.date()

                    bet_start = (f.expire).date()

                    if date == bet_start:
                        start = f.expire + datetime.timedelta(hours=5, minutes=30)
                        print(start)
                        start = start.time()
                        today = 'yes'
                    else:
                        start = f.expire + datetime.timedelta(hours=5, minutes=30)

                        today = "no"
                    betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
                    betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
                    try:
                        total_wagered = betting_against + betting_for
                        bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                        bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                            'bet_against']
                        totl = bet_against + bet_for
                        percent_for = (bet_for / totl) * 100
                        percent_against = (100 - percent_for)

                        total = Betting.objects.filter(forecast=f).count()
                    except Exception:
                        total_wagered = 0
                        percent_for = 0
                        percent_against = 0
                        bet_for = 0
                        bet_against = 0
                        total = Betting.objects.filter(forecast=f).count()
                    data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=f,
                                     total=total, start=start, total_user=betting_for + betting_against,
                                     betting_for=betting_for, betting_against=betting_against, today=today,
                                     participants=total_wagered, bet_for=bet_for,
                                     bet_against=bet_against))
                return render(request, 'search_data.html',
                              {"live": data,
                               "user": "Guest" if request.user.is_anonymous() else request.user.username,
                               "heading": "Search Forecast",
                               "title": "Search Forecast",
                               })
    else:
        return render(request, "search_data_nf.html", {"data": "No result found", "heading": "Search Forecast",
                                                       "title": "Search Forecast",
                                                       "user": "Guest" if request.user.is_anonymous() else request.user.username})


@csrf_exempt
def signup_page(request):
    if request.method == 'POST':

        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        email = request.POST.get('email', '')
        if not username or not password or not email:
            return HttpResponse(json.dumps(dict("Please fill all details")))
        else:
            try:
                user = User.objects.get(email=email)
                return HttpResponse(json.dumps(dict(message="User Already exists")))
            except Exception:
                user = User.objects.create(email=email, username=username)
                user.set_password(password)
                sa = SocialAccount.objects.create(user=user, uid=random.randint(1000, 100000), )
                sa.save()
                user.save()
                return HttpResponse(json.dumps(dict(status=200)))
    else:
        return render(request, 'signup.html')


@csrf_exempt
def login_page(request):
    if request.method == 'POST':
        password = request.POST.get('password', '')
        email = request.POST.get('email', '')
        if not password or not email:
            return HttpResponse(json.dumps(dict("Please fill all details")))
        else:
            try:
                users = authenticate(request, username=email, password=password)
                if users:
                    login(request, users)
                    return HttpResponse(json.dumps(dict(status=200)))
                else:
                    return HttpResponse(json.dumps(dict(status="Please try again")))

            except Exception:
                return HttpResponse(json.dumps(dict(message="Please try again.")))
    else:
        return render(request, 'login.html')


@csrf_exempt
def get_forecast(request):
    if request.method == "POST":
        forecast = ForeCast.objects.get(id=request.POST.get('id', ''))
        return render_to_response('forecast_modal.html',
                                  {'forecast': forecast}, )
    else:

        return HttpResponse(json.dumps(dict(error="Try again later")))


def not_approved(forecast):
    data = []

    for f in forecast:
        date = current.date()
        forecast = f.forecast
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            today = "no"
        data.append(dict(percent_for=0, percent_against=0, forecast=f,
                         total=0, start=start, total_user=0,
                         betting_for=0, betting_against=0, today=today,
                         participants=0, bet_for=0,
                         bet_against=0))
        print(data)
    return data


def live_forecast_data_bet(forecast_live, account):
    data = []

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = f.expire + datetime.timedelta(hours=5, minutes=30)
            print(start)
            start = start.time()
            today = 'yes'
        else:
            start = f.expire + datetime.timedelta(hours=5, minutes=30)

            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = 0
            bet_against = 0
            bet_against_user = 0
            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against,
                         bet_against_user=bet_against_user if bet_against_user else 0,
                         bet_for_user=bet_for_user if bet_for_user else 0
                         ))
    return data


def live_forecast_data_private(forecast_live, account):
    data = []

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = forecast.expire.date()

        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
                Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = 0
            bet_against = 0
            bet_against_user = 0
            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against,
                         bet_against_user=bet_against_user if bet_against_user else 0,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         ))
    return data


def live_forecast_data(forecast_live, account):
    data = []

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = 0
            bet_against = 0
            bet_against_user = 0
            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against,
                         bet_against_user=bet_against_user if bet_against_user else 0,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         ))
    return data


def forecast_invite_data(forecast_live, account):
    data = []
    for f in forecast_live:
        forecast = f.forecast
        date = current.date()
        bet_start = (forecast.expire).date()
        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = forecast.start + datetime.timedelta(hours=5, minutes=30)
            today = 'no'
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            total_wagered = betting_against + betting_for
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = bet_for + bet_against
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = 0
            bet_against = 0
            bet_against_user = 0
            total = 0
        status = 'yes' if forecast.won == "yes" else 'no'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won="Yes" if forecast.won == 'yes' else 'No',  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         bet_against_user=bet_against_user if bet_against_user else 0
                         ))

    return data


def forecast_result_data(forecast_live, account):
    data = []
    for f in forecast_live:
        print(f)
        forecast = f.forecast
        date = current.date()
        bet_start = forecast.expire.date()
        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = forecast.start + datetime.timedelta(hours=5, minutes=30)
            today = 'no'
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            total_wagered = betting_against + betting_for
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = bet_for + bet_against
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = 0
            bet_against = 0
            bet_against_user = 0
            total = 0
        status = 'yes' if forecast.won == "yes" else 'no'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won="Yes" if forecast.won == 'yes' else 'No',  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         bet_against_user=bet_against_user if bet_against_user else 0
                         ))

    return data


def forecast_result_data_private(forecast_live, account):
    data = []
    for f in forecast_live:
        forecast = f
        date = current.date()
        bet_start = forecast.expire.date()
        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = forecast.start + datetime.timedelta(hours=5, minutes=30)
            today = 'no'
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=account).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            total_wagered = betting_against + betting_for
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = bet_for + bet_against
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = 0
            bet_against = 0
            bet_against_user = 0
            total = 0
        status = 'yes' if forecast.won == "yes" else 'no'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won="Yes" if forecast.won == 'yes' else 'No',  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         bet_against_user=bet_against_user if bet_against_user else 0
                         ))

    return data


def my_forecast_private(request):
    try:
        user = request.user.id
        users = User.objects.get(id=user)
        account = SocialAccount.objects.get(user=users)
        forecast_live = ForeCast.objects.filter(approved__name="yes", status__name='In-Progress',
                                                user=account, private__name='yes').order_by("expire")

        forecast_result = ForeCast.objects.filter(approved__name="yes", status__name='Result Declared',
                                                  user=account, private__name='yes').order_by("expire")
        forecast_approval = InviteFriends.objects.filter(user=account).order_by("-forecast__expire")

        return render(request, 'my_friend_private.html', {"live": live_forecast_data_private(forecast_live, account),
                                                          "result": forecast_result_data_private(forecast_result,
                                                                                                 account),
                                                          "approval": forecast_invite_data(forecast_approval, account),
                                                          "user": "Guest" if request.user.is_anonymous() else request.user.username,
                                                          "heading": "Forecast Private",
                                                          "title": "My Forecast",
                                                          })
    except Exception:
        return render(request, 'my_friend_nl.html',
                      {"user": "Guest" if request.user.is_anonymous() else request.user.username,
                       "heading": "Forecast Private",
                       "title": "My Forecast",
                       })


@csrf_exempt
def get_sub_cat(request):
    if request.method == "POST":
        cat = Category.objects.get(id=int(request.POST.get('identifier', '')))
        sub = SubCategory.objects.filter(category=cat).order_by('identifier')
        data = [dict(id=x.id, name=x.name) for x in sub]
        return HttpResponse(json.dumps(dict(data=data, source=sub[0].source)))


@csrf_exempt
def get_sub_source(request):
    if request.method == "POST":
        cat = SubCategory.objects.get(id=int(request.POST.get('identifier', '')))
        return HttpResponse(json.dumps(cat.source))


def forecast_live_view(category, profile):
    data = []
    forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no', category=category,
                                            status__name='In-Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = f.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = f.expire + datetime.timedelta(hours=5, minutes=30)

            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=profile).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=profile).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            print(percent_for, percent_against)

            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = bet_against_user = 0
            bet_against = 0

            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against,
                         bet_against_user=bet_against_user if bet_against_user else 0,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         ))
    return data


def forecast_live_view_sub(category, profile):
    data = []
    forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no', sub_category=category,
                                            status__name='In-Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=forecast, users=profile).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
            Betting.objects.filter(forecast=forecast, users=profile).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            print(percent_for, percent_against)

            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = bet_against_user = 0
            bet_against = 0

            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against,
                         bet_against_user=bet_against_user if bet_against_user else 0,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         ))
    return data


def forecast_live_view_bt(category_id):
    data = []
    forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no', category=category_id,
                                            status__name='In-Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = f.expire + datetime.timedelta(hours=5, minutes=30)
            print(start)
            start = start.time()
            today = 'yes'
        else:
            start = f.expire + datetime.timedelta(hours=5, minutes=30)

            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            print(percent_for, percent_against)

            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = bet_against_user = 0
            bet_against = 0

            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against, bet_against_user=0,
                         bet_for_user=0,
                         ))
    return data


def forecast_live_view_bt_sub(category_id):
    data = []
    forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no', sub_category=category_id,
                                            status__name='In-Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            start = start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = bet_against + bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            print(percent_for, percent_against)

            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_for_user = bet_against_user = 0
            bet_against = 0

            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against, bet_against_user=0,
                         bet_for_user=0,
                         ))
    return data


def e_handler404(request):
    context = RequestContext(request)
    response = render_to_response('404.html', context)
    response.status_code = 404
    return response


def e_handler500(request):
    context = RequestContext(request)
    response = render_to_response('500.html', context)
    response.status_code = 500
    return response


def update_close_status(request):
    now = datetime.datetime.now()
    status = Status.objects.get(name='Closed')
    ForeCast.objects.filter(approved=True, expire__lte=now, status__name='In-Progress').update(status=status)
    return HttpResponse("updated")


def privacy(request):
    return render(request, 'privacy_policy.html')


def terms(request):
    return render(request, 'terms.html')
    # with open('/home/lawrato/forecastguru/static/docs/terms.pdf', 'r') as pdf:
    #     response = HttpResponse(pdf.read(), content_type='application/pdf')
    #     response['Content-Disposition'] = 'inline;filename=some_file.pdf'
    #     return response


def faq(request):
    return render(request, 'faq.html')

    # with open('/home/lawrato/forecastguru/static/docs/FAQ.pdf', 'r') as pdf:
    #     response = HttpResponse(pdf.read(), content_type='application/pdf')
    #     response['Content-Disposition'] = 'inline;filename=some_file.pdf'
    #     return response


def facebook_category(request):
    username = request.GET.get('username', '')
    email = request.GET.get('email', '')
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    uid = request.GET.get('uid', '')
    extra_data = {"usernam": username, "email": email, "first_name": first_name, "last_name": last_name, "uid": uid}
    response = HttpResponse('test')
    try:
        user = User.objects.get(username=username, email=email, first_name=first_name, last_name=last_name)
        set_cookie(response, "sessionid", uid)
        set_cookie(response, "csrftoken", "RPlsDgOhRDyJDHrJvfodNKw7dFMT8Jd1JHiuBCRQLrgqH7Z5i1wR8lk0q50OSTi4")
        hasher = hashlib.md5(str(user.id).encode())
        request.session['_auth_user_hash'] = hasher.hexdigest()
        request.session['_auth_user_id'] = user.id
        request.session['_auth_user_backend'] = "django.contrib.auth.backends.ModelBackend"
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

    except Exception:
        user = User.objects.create(username=username, email=email, first_name=first_name, last_name=last_name)
        social = SocialAccount.objects.create(user=user, provider='facebook', uid=uid, extra_data=extra_data)
        user = User.objects.get(username=username)
        set_cookie(response, "sessionid", uid)
        set_cookie(response, "csrftoken", "RPlsDgOhRDyJDHrJvfodNKw7dFMT8Jd1JHiuBCRQLrgqH7Z5i1wR8lk0q50OSTi4")
        hasher = hashlib.md5(str(user.id).encode())
        request.session['_auth_user_hash'] = hasher.hexdigest()
        request.session['_auth_user_id'] = user.id
        request.session['_auth_user_backend'] = "django.contrib.auth.backends.ModelBackend"
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    # category = Category.objects.all().order_by('name')
    #     set_cookie(response, "sessionid", uid)
    #     set_cookie(response, "csrftoken", "RPlsDgOhRDyJDHrJvfodNKw7dFMT8Jd1JHiuBCRQLrgqH7Z5i1wR8lk0q50OSTi4")
    #     hasher = hashlib.md5(str(user.id).encode())
    #     request.session['_auth_user_hash'] = hasher.hexdigest()
    #     request.session['_auth_user_id'] = user.id
    #     request.session['_auth_user_backend'] = "django.contrib.auth.backends.ModelBackend"
    return render(request, 'category.html', {'category': category,
                                             "heading": "Categories",
                                             "title": "Categories",
                                             "user": "Guest" if request.user.is_anonymous() else request.user.username})


def set_cookie(response, key, value, days_expire=7):
    if days_expire is None:
        max_age = 365 * 24 * 60 * 60  # one year
    else:
        max_age = days_expire * 24 * 60 * 60
    expires = datetime.datetime.strftime(datetime.datetime.utcnow() + datetime.timedelta(seconds=max_age),
                                         "%a, %d-%b-%Y %H:%M:%S GMT")
    response.set_cookie(key, value, max_age=max_age, expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        secure=settings.SESSION_COOKIE_SECURE or None)


def session(request):
    return HttpResponse(json.dumps(dict(keys=request.session.keys(), values=request.session.values())))


@staff_member_required
@csrf_exempt
def import_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not CSV type')
            return HttpResponseRedirect("/import_csv/")
        # if file is too large, return
        if csv_file.multiple_chunks():
            messages.error(request, "Uploaded file is too big (%.2f MB)." % (csv_file.size / (1000 * 1000),))
            return HttpResponseRedirect("/import_csv/")

        file_data = csv_file.read().decode("utf-8")

        lines = file_data.split("\n")
        # loop over the lines and save them in db. If error , store as string and then display
        for i in range(len(lines) - 1):
            fields = lines[i].split(",")
            try:
                private = Private.objects.get(name='no')
            except Exception:
                return HttpResponse("Error - In Private field")
            try:
                status = Status.objects.get(name='In-Progress')
            except Exception:
                return HttpResponse("Error - In Status field")
            try:
                verified = Verified.objects.get(name='no')
            except Exception:
                return HttpResponse("Error - In Verified field")
            try:
                category = Category.objects.get(name__icontains=str(fields[0]))
            except Exception:
                return HttpResponse("Error - In Category field")
            try:
                sub_category = SubCategory.objects.get(name__icontains=str(fields[1]))
            except Exception:
                return HttpResponse("Error - In Sub Category field")
            try:
                user = User.objects.get(username=str(fields[3]))
                social = SocialAccount.objects.get(user=user)
            except Exception:
                return HttpResponse("Error - In User Name field")
            try:
                approved = Approved.objects.get(name=str(fields[5]))
            except Exception:
                return HttpResponse("Error - In Approved field")
            try:
                expire = datetime.datetime.strptime(str(fields[4]), "%Y-%m-%d %H:%M:%S")
            except Exception:
                return HttpResponse("Error - In Expire field")
            try:
                heading = fields[2]
            except Exception:
                return HttpResponse("Error - In Heading field")
            try:
                f = ForeCast.objects.get(category=category, sub_category=sub_category, user=social,
                                         heading=fields[2], approved=approved, verified=verified,
                                         private=private, expire=expire, created=datetime.datetime.now().date(),
                                         status=status)

            except Exception:
                f = ForeCast.objects.create(category=category, sub_category=sub_category, user=social,
                                            heading=heading, approved=approved, verified=verified,
                                            private=private, expire=expire, created=datetime.datetime.now().date(),
                                            status=status)
                f.user.forecast_created += 1
                f.user.save()
                f.save()
                yes = randrange(1000, 9000, 1000)
                no = randrange(1000, 9000, 1000)
                admin = SocialAccount.objects.get(user__username="admin")
                Betting.objects.create(forecast=f, users=admin, bet_for=yes, bet_against=no)

        return HttpResponse(json.dumps(dict(message="File Uploaded Successful")))
    else:
        return render(request, 'import_csv.html', {"heading": "Import CSV",
                                                   "title": "Import CSV", })


def device_data_android(request):
    if request.method == "GET":
        username = request.GET.get('username', "")
        device_id = request.GET.get('device_id', "")
        device_token = request.GET.get('device_token', "")
        if username == '' or device_token == '' or device_id == '':
            return HttpResponse(json.dumps(dict(message='Not Save', status=400)))
        try:
            user = User.objects.get(username=username)
            social = SocialAccount.objects.get(user=user)
            tokens = UserDevice.objects.get(user=social, device_id=device_id)
            tokens.device_token = device_token
            tokens.save()
            return HttpResponse(json.dumps(dict(message='Saved', status=200)))
        except Exception:
            user = User.objects.get(username=username)
            social = SocialAccount.objects.get(user=user)
            UserDevice.objects.create(user=social, device_id=device_id, device_token=device_token)
            return HttpResponse(json.dumps(dict(message='Saved', status=200)))


def thank_you(request):
    try:
        user = request.user
        profile = SocialAccount.objects.get(user=user)
        status = LoginStatus.objects.get(user=profile)
        if status.status == 1:
            return HttpResponseRedirect("/category/")
        else:
            status.status = 1
            status.save()
            return render(request, "thank_you.html", {"heading": "Registration Complete",
                                                      "title": "Registration Complete", })
    except Exception:
        user = request.user
        profile = SocialAccount.objects.get(user=user)
        LoginStatus.objects.create(user=profile, status=1)

        return render(request, "thank_you.html", {"heading": "Registration Complete",
                                                  "title": "Registration Complete", })


@csrf_exempt
def invite_friends(request):
    if request.method == 'POST':
        try:
            user = request.user
            profile = SocialAccount.objects.get(user=user)

            forecast_id = request.POST.get('forecast_id')
            forecast = ForeCast.objects.get(id=forecast_id)
            try:
                InviteFriends.objects.get(forecast=forecast, user=profile)
                return HttpResponse(json.dumps(dict(message="success")))
            except Exception:
                InviteFriends.objects.create(forecast=forecast, user=profile)
                return HttpResponse(json.dumps(dict(message="success")))
        except Exception:
            return HttpResponse(json.dumps(dict(message="false")))


def trending_forecast(request):
    current = datetime.datetime.now().date().strftime("%Y-%m-%d")
    forecast = ForeCast.objects.filter(expire__gte=current + " 00:00:00", status__name='In-Progress',private__name='no',)
    data = []
    for f in forecast:
        bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
        bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
            'bet_against']
        if bet_for + bet_against > 5000:
            data.append(f)

    if len(data) == 0:
        return render(request, "no_trending.html", {"heading": "Trending Forecast", "title": "Trending Forecast", })
    else:

        objects = data[:10]

        for f in objects:
            date = datetime.datetime.now().date()
            forecast = f
            bet_start = forecast.expire.date()
            if date == bet_start:
                start = forecast.expire + datetime.timedelta(hours=5, minutes=30)
                print(start)
                start = start.time()
                today = 'yes'
            else:
                start = forecast.expire

                today = "no"
            betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
            betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
            try:
                total_wagered = betting_against + betting_for
                bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
                bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
                totl = bet_against + bet_for
                percent_for = (bet_for / totl) * 100
                percent_against = (100 - percent_for)

                total = Betting.objects.filter(forecast=forecast).count()
            except Exception:
                total_wagered = 0
                percent_for = 0
                percent_against = 0
                bet_for = 0
                bet_against = 0
                total = Betting.objects.filter(forecast=forecast).count()
            data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast.heading,
                             total=total, start=start, total_user=betting_for + betting_against,
                             betting_for=betting_for, betting_against=betting_against, today=today,
                             participants=total_wagered, bet_for=bet_for,
                             bet_against=bet_against,
                             bet_for_user=0,
                             bet_against_user=0))

        return render(request, 'trending.html',
                      {"live": data, "heading": "Trending Forecast", "title": "Trending Forecast", })


def main_page(request):
    user = request.user
    try:
        users = User.objects.get(username=user.username)
        account = SocialAccount.objects.get(user=users)
        return HttpResponseRedirect("/category/")
    except Exception:
        return render(request, 'main_page.html')