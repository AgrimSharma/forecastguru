# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
import json, random
from django.shortcuts import render, HttpResponseRedirect, redirect, render_to_response
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from authentication.models import *
import re
from random import randrange
import datetime
from django.template import RequestContext
from paytm.payments import PaytmPaymentPage
from paytm import Checksum
from django.http import HttpResponse
from paytm.payments import VerifyPaytmResponse,JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from allauth.socialaccount.models import SocialAccount, SocialToken

current = datetime.datetime.now()


def id_generator(fname, lname):
    r = re.compile(r"\s+", re.MULTILINE)
    return r.sub("", str(fname)).capitalize() + str(lname).capitalize() + str(random.randrange(1111, 9999))


def main_login_after(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        auth = Authentication.objects.get(facebook_id=users.uid)
    except Exception:
        users = SocialAccount.objects.get(user=request.user)
        user = request.user
        user.username = users.uid
        user.save()
        fuser = Authentication.objects.create(facebook_id=users.uid, first_name=user.first_name, last_name=user.last_name,
                                              email=user.email)
        fuser.referral_code = id_generator(users.user.first_name, users.user.last_name)
        fuser.points_earned = JoiningPoints.objects.latest('id').points
        fuser.save()
    return redirect("/referral_code/")


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        userID = request.POST.get('userID')
        first_name = request.POST.get('first_name', "")
        last_name = request.POST.get('last_name', "")
        email = request.POST.get('email', "")
        try:
            user = User.objects.get(username=userID)
            auth = authenticate(request, username=userID, password=userID)

            if auth:
                login(request, auth)
            return HttpResponse("registered")
        except Exception:
            user = User.objects.create(username=userID,
                                       email=email,
                                       first_name=first_name,
                                       last_name=last_name
                                       )
            fuser = Authentication.objects.create(facebook_id=userID,
                                                  first_name=first_name,
                                                  last_name=last_name,
                                                  email=email
                                                  )
            fuser.referral_code = id_generator(first_name, last_name)
            fuser.points_earned = JoiningPoints.objects.latest('id').points
            fuser.save()
            user.set_password(userID)
            user.save()
            auth = authenticate(request, username=userID, password=userID)
            if auth:
                login(request, auth)
            return HttpResponse("success")
    else:
        try:
            user = request.user.username
            auth = Authentication.objects.get(facebook_id=user)
            return redirect("/referral_code/")
        except Exception:
            return render(request, "home/index.html", {
                "points": JoiningPoints.objects.latest('id').points
            })


def index(request):
    try:
        user = request.user.username
        auth = Authentication.objects.get(facebook_id=user)
        return redirect("/live_forecast/")
    except Exception:
        joining = JoiningPoints.objects.latest('id')
        return render(request, "home/main_page.html", {
            "points": joining.points
        })


@login_required
def referral_code(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        fuser = Authentication.objects.get(facebook_id=users.uid)
        if fuser.referral_status == 0:
            total = fuser.joining_points + fuser.points_won_public + fuser.points_won_private + fuser.points_earned \
                    - fuser.points_lost_public - fuser.points_lost_private
            return render(request, "home/referral_code.html", {
                "first_name": fuser.first_name,
                "total": total
            })
        else:
            return redirect("/interest_select/")
    except Exception:
        users = SocialAccount.objects.get(user=request.user)
        user = request.user
        user.username = users.uid
        user.save()
        fuser1 = Authentication.objects.filter(facebook_id=users.uid)
        if len(fuser1) == 0:
            fuser = Authentication.objects.create(facebook_id=users.uid, first_name=user.first_name, last_name=user.last_name,
                                                  email=user.email)
            fuser.referral_code = id_generator(users.user.first_name, users.user.last_name)
            fuser.points_earned = JoiningPoints.objects.latest('id').points

            if fuser.referral_status == 0:
                total = int(fuser.joining_points) + int(fuser.points_won_public) + int(fuser.points_won_private) + int(fuser.points_earned) - int(fuser.points_lost_public) - int(fuser.points_lost_private)
                fuser.save()
                return render(request, "home/referral_code.html", {
                    "first_name": fuser.first_name,
                    "total": total
                })
        else:
            return redirect("/interest_select/")


@login_required
@csrf_exempt
def check_referral(request):
    if request.method == "POST":
        code = request.POST.get('referral_code')
        try:
            users = SocialAccount.objects.get(user=request.user)
            reff = Authentication.objects.get(referral_code=code)
            auth = Authentication.objects.get(facebook_id=users.uid)
            auth.referral_status = 2
            auth.save()
            return HttpResponse("success")
        except Exception:
            return HttpResponse("error")

    else:
        users = SocialAccount.objects.get(user=request.user)
        auth = Authentication.objects.get(facebook_id=users.uid)
        auth.referral_status = 1
        auth.save()
        return redirect("/interest_select/")


@login_required
@csrf_exempt
def interest(request):
    if request.method == 'GET':
        try:
            users = SocialAccount.objects.get(user=request.user)
            profile = Authentication.objects.get(facebook_id=users.uid)
            interest = UserInterest.objects.filter(user=profile)
            total = profile.joining_points + profile.points_won_public\
                    + profile.points_won_private + profile.points_earned - profile.points_lost_public - profile.points_lost_private
            if len(interest) == 0 and profile.interest_status == 0:
                sub = Category.objects.all().order_by('id')
                return render(request, "home/interest_select.html", {
                    "sub": sub,
                    "heading": "Select Interest",
                    "title": "ForecastGuru",
                    "first_name": request.user.first_name,
                    "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                    "total": total
                })
            else:

                return redirect("/live_forecast/")

        except Exception:
            return redirect("/login/")
    elif request.method == "POST":

        data = request.POST.getlist('data[]',"")
        if len(data) == 0:
            return HttpResponse("interest")
        elif len(data) > 0:
            interest = [int(d) for d in data]
            interest_list = SubCategory.objects.filter(id__in=interest)
            try:
                users = SocialAccount.objects.get(user=request.user)
                profile = Authentication.objects.get(facebook_id=users.uid)
                for i in interest_list:
                    interest = UserInterest.objects.filter(user=profile, interest=i)
                    if len(interest) == 0:
                        u = UserInterest.objects.create(user=profile, interest=i)
                        u.save()
                profile.interest_status = 1
                profile.save()
                return HttpResponse("success")
            except Exception:
                return HttpResponse("login")


@login_required
def interest_skip(request):
    users = SocialAccount.objects.get(user=request.user)
    auth = Authentication.objects.get(facebook_id=users.uid)
    auth.interest_status = 1
    auth.save()
    return redirect("/live_forecast/")


@login_required
def live_forecast(request):
    data = []
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        today = datetime.datetime.now().date()
        diff = today - profile.last_login
        if diff.days == 1:
            profile.login_count += 1
            days = DailyFreePoints.objects.get(days=profile.login_count).points
            profile.points_earned += days
            profile.last_login = today
            profile.save()
        elif diff.days == 0:
            pass
        else:
            profile.last_login = today
            profile.login_count = 0
            profile.save()
        interest = UserInterest.objects.filter(user=profile)
        intrest = [i.interest.id for i in interest]
        forecast_live = ForeCast.objects.filter(status__name='Progress',
                                                sub_category__id__in=intrest).order_by("-expire")
    except Exception:
        forecast_live = ForeCast.objects.filter(status__name='Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()

        bet_start = f.expire.date()
        if date == bet_start:
            start = f.expire
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
            totl = float(bet_against + bet_for)
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = Betting.objects.filter(forecast=f).count()
        except Exception:
            total_wagered = 0
            bet_against_user = 0
            bet_for_user = 0
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))['bet_against']
            totl = float(bet_against + bet_for)
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            total = Betting.objects.filter(forecast=f).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=f,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         bet_against_user=bet_against_user if bet_against_user else 0))
    return render(request, 'home/live_forecast.html',
                  {
                      "live": data,
                      "heading": "Forecasts",
                      "title": "ForecastGuru",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name
                  })


@login_required
def live_forecast_descending(request):
    data = []
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        interest = UserInterest.objects.filter(user=profile)
        intrest = [i.interest.id for i in interest]
        forecast_live = ForeCast.objects.filter(status__name='Progress',
                                                sub_category__id__in=intrest).order_by("expire")
    except Exception:
        forecast_live = ForeCast.objects.filter(status__name='Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()

        bet_start = f.expire.date()
        if date == bet_start:
            start = f.expire
            start = start.time()
            today = 'Yes'
        else:
            start = f.expire

            today = "No"
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
        try:
            import pdb;pdb.set_trace()
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_for_user = Betting.objects.filter(forecast=f, users=profile).aggregate(bet_for=Sum('bet_for'))[
                'bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            bet_against_user = \
                Betting.objects.filter(forecast=f, users=profile).aggregate(bet_against=Sum('bet_against'))[
                    'bet_against']
            totl = float(bet_against + bet_for)
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
    return render(request, 'home/live_forecast.html', {"live": data,
                                                       "heading": "Forecasts",
                                                       "title": "ForecastGuru",
                                                       "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name})


@csrf_exempt
def bet_post(request):
    if request.method == 'POST':
        try:
            users = SocialAccount.objects.get(user=request.user)
            account = Authentication.objects.get(facebook_id=users.uid)
        except Exception:
            return HttpResponse(json.dumps(dict(message='login')))
        vote = request.POST.get('vote')
        points = int(request.POST.get('points'))
        if int(points) % 1000 != 0:
            return HttpResponse(json.dumps(dict(message='Points should be multiple of 1000')))
        forecast = request.POST.get('forecast')
        forecasts = ForeCast.objects.get(id=forecast)
        if account.points_earned - points > 0 or account.points_won_public - points > 0 or account.points_won_private- points > 0:
            try:
                b = Betting.objects.get(forecast=forecasts, users=account)
                if vote == 'email':
                    b.bet_for += points
                    if b.users.points_earned >= points:
                        b.users.points_earned -= points
                    elif b.users.points_won_public >= points:
                        b.users.points_won_public -= points
                    else:
                        b.users.points_won_private -= points
                    b.users.save()
                    b.save()
                else:
                    b.bet_against += points
                    if b.users.points_earned >= points:
                        b.users.points_earned -= points
                    elif b.users.points_won_public >= points:
                        b.users.points_won_public -= points
                    else:
                        b.users.points_won_private -= points
                    b.users.save()
                    b.save()
            except Exception:
                if vote == 'email':
                    b = Betting.objects.create(forecast=forecasts, users=account, bet_for=points, bet_against=0)
                    if b.users.points_earned >= points:
                        b.users.points_earned -= points
                    elif b.users.points_won_public >= points:
                        b.users.points_won_public -= points
                    else:
                        b.users.points_won_private -= points
                    b.users.forecast_participated += 1
                    b.users.save()
                    b.save()
                else:
                    b = Betting.objects.create(forecast=forecasts, users=account, bet_for=0, bet_against=points)
                    if b.users.points_earned >= points:
                        b.users.points_earned -= points
                    elif b.users.points_won_public >= points:
                        b.users.points_won_public -= points
                    else:
                        b.users.points_won_private -= points
                    b.users.forecast_participated += 1
                    b.users.save()
                    b.save()
                notif = UserNotifications.objects.create(user=account, forecast=forecasts)
                notif.save()
            return HttpResponse(json.dumps(dict(message='success', heading=forecasts.heading, id=forecasts.id)))
        else:
            return HttpResponse(json.dumps(dict(message='balance')))
    else:
        return HttpResponse(json.dumps(dict(message='Please use POST')))



@csrf_exempt
def get_forecast(request):
    if request.method == "POST":
        try:
            users = SocialAccount.objects.get(user=request.user)
            profile = Authentication.objects.get(facebook_id=users.uid)
            forecast = ForeCast.objects.get(id=request.POST.get('id', ''))
            return HttpResponse(json.dumps(dict(heading=forecast.heading, id=forecast.id)))
        except Exception:
            return HttpResponse(json.dumps(dict(error="login")))
    else:

        return HttpResponse(json.dumps(dict(error="Try again later")))


@csrf_exempt
def create_forecast(request):
    if request.method == 'POST':
        current = datetime.datetime.now()
        category = request.POST.get('category', '')
        sub_category = request.POST.get('sub_cat', '')
        tags = request.POST.get('tags', '')
        heading = request.POST.get('heading', '')
        time = request.POST.get('time', '')
        date = request.POST.get('date', '')
        cat = Category.objects.get(id=category)
        sub_cat = SubCategory.objects.get(id=sub_category)
        expires = datetime.datetime.strptime(date + " " + time, "%d/%m/%Y %I:%M %p")

        if expires < current:
            return HttpResponse(json.dumps(dict(status=400, message='end')))
        try:
            user = SocialAccount.objects.get(user=request.user)
            users = Authentication.objects.get(facebook_id=user.uid)
        except Exception:
            return HttpResponse(json.dumps(dict(status=400, message='Please Login')))
        private = Private.objects.get(id=1)
        status = Status.objects.get(name='Progress')
        ForeCast.objects.create(category=cat, sub_category=sub_cat,
                                user=users, heading=heading,
                                expire=expires,
                                status=status, created=current,
                                private=private, tags=tags
                                )
        f = ForeCast.objects.get(category=cat, sub_category=sub_cat,
                                 user=users, heading=heading,
                                 )
        f.user.forecast_created += 1
        f.user.save()
        f.save()
        Yes = randrange(1000, 9000, 1000)
        No = randrange(1000, 9000, 1000)
        admin = Authentication.objects.get(facebook_id="admin")
        bet = Betting.objects.create(forecast=f, users=admin, bet_for=Yes, bet_against=No)
        bet.save()
        notif = UserNotifications.objects.create(user=users, forecast=f)
        notif.save()
        return HttpResponse(json.dumps(
            dict(status=200, message='Thank You for creating a private forecast', id=f.id)))

    else:
        try:
            users = SocialAccount.objects.get(user=request.user)
            profile = Authentication.objects.get(facebook_id=users.uid)
            category = Category.objects.all().order_by('identifier')
            return render(request, 'home/create_forecast.html', {
                'category': category,
                "current": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                "heading": "Create Forecast",
                "title": "ForecastGuru",
            })
        except Exception:
            return render(request, 'home/create_forecast_nl.html', {
                "heading": "Create Forecast",
                "title": "ForecastGuru",
                "user": "Guest" if request.user.is_anonymous() else request.user.first_name, })


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


def betting(request, userid):
    forecast = ForeCast.objects.get(id=userid)
    approved = "Yes" if forecast.private.name == 'Yes' and forecast.status.name == 'Progress' else 'No'
    if forecast.status.name == 'Progress':
        status = 'Currently Live'
    elif forecast.status.name == 'Closed':
        status = 'Currently Closed'
    else:
        status = 'Result Declared'
    expires = forecast.expire
    end_date = datetime.datetime.strftime(expires, '%b %d, %Y')
    end_time = datetime.datetime.strftime(expires, '%H:%M')
    # try:/
    if request.user.is_anonymous():
        users = "Guest"
    else:
        users = request.user.username
    if forecast.private.name == 'No':
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        betting_sum = Betting.objects.filter(forecast=forecast).aggregate(
            bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
        try:
            total_wagered = betting_sum['bet_for'] + betting_sum['bet_against']
        except Exception:
            total_wagered = 0

        try:
            percent = round((betting_for / (betting_for + betting_against)) * 100, 2)
        except Exception:
            percent = 0
        try:
            success = Authentication.objects.get(facebook_id=request.user.username)
            success = success.successful_forecast
        except Exception:
            success = 0
        try:
            sums = betting_sum['bet_for'] + betting_sum['bet_against']
        except Exception:
            sums = 0

        try:
            social = Authentication.objects.get(facebook_id=request.user.username)
            bet_for_user = Betting.objects.get(forecast=forecast, users=social).bet_for
            bet_against_user = Betting.objects.get(forecast=forecast, users=social).bet_against
            market_fee = sums * 0.10 if forecast.user == social else 0
        except Exception:
            bet_against_user = 0
            bet_for_user = 0
            market_fee = 0
        if forecast.won.name == "Yes":
            ratio = round(betting_sum['bet_for'] / sums, 2) + 1
            earned = bet_for_user * ratio
            market_fee_paid = earned * 0.10
            total_earning = earned - market_fee_paid + market_fee
        elif forecast.won.name == "No":
            ratio = round(betting_sum['bet_against'] / sums, 2) + 1
            earned = bet_against_user * ratio
            market_fee_paid = earned * 0.10
            total_earning = earned - market_fee_paid + market_fee
        else:
            ratio = "NA"
            earned = 0
            market_fee_paid = earned * 0.10
            total_earning = earned - market_fee_paid + market_fee
        return render(request, 'home/betting.html',
                      {
                          'forecast': forecast, 'betting': betting,
                          'bet_for': betting_sum['bet_for'] if betting_sum['bet_for'] else 0,
                          'against': betting_sum['bet_against'] if betting_sum['bet_against'] else 0,
                          'total': total_wagered if total_wagered else 0,
                          "end_date": end_date,
                          "end_time": end_time,
                          'status': status,
                          "percent": percent,
                          "success": success,
                          "users": request.user.username,
                          "sums": sums,"earned": int(earned),
                          "approved": approved,
                          "ratio": ratio,
                          "user": users,
                          "won": forecast.won.name,
                          "market_fee_paid": int(market_fee_paid),
                          "heading": "Forecast Details",
                          "title": "ForecastGuru",
                          "private": "no",
                          "bet_against_user": bet_against_user,
                          "bet_for_user": bet_for_user,
                          "market_fee": int(market_fee),
                          "total_earn": int(total_earning)
                      })
    elif forecast.private.name == 'Yes':
        points = []
        betting_sum = Betting.objects.filter(forecast=forecast).aggregate(
            bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
        try:
            sums = betting_sum['bet_for'] + betting_sum['bet_against']
        except Exception:
            sums = 0
        if forecast.won.name == "Yes":
            ratio = round(betting_sum['bet_for'] / sums, 2) + 1
            won = "Yes"
        elif forecast.won.name == "No":
            ratio = round(betting_sum['bet_against'] / sums, 2) + 1
            won = "No"
        else:
            ratio = "NA"
            won = "NA"
        return render(request, 'home/betting.html', {
            'forecast': forecast,
            'betting': betting,
            "approved": approved,
            "user": users,'status': status,
            "users": forecast.user.first_name,
            "end_date": end_date,
            "end_time": end_time,
            "won": won,"ratio": ratio,
            "heading": "Forecast Details",
            "title": "ForecastGuru",
            "private": "yes",
            "points": points
        })


@csrf_exempt
def result_save(request):
    if request.method == "POST":
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        vote = request.POST.get("vote","")
        id = request.POST.get('forecast', '')
        if vote == 'email':
            vote = 'Yes'
        else:
            vote = 'No'

        verified = Verified.objects.get(id=1)
        status = Status.objects.get(name='Closed')
        forecast = ForeCast.objects.get(id=int(id))
        ForeCast.objects.filter(id=id).update(won=vote, status=status, verified=verified)
        return HttpResponse(request.path)
    else:
        return HttpResponse(json.dumps(dict(error="Try again later")))


def forecast_result_page(forecast):
    data = []
    for f in forecast:
        date = current.date()
        bet_start = f.expire.date()
        if date == bet_start:
            start = f.expire
            start = start.time()
            today = 'Yes'
        else:
            start = f.expire
            today = 'No'
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            total_wagered = betting_against + betting_for
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
            percent_against = (100 - percent_for)
            total = bet_against + bet_for
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_against = 0
            total = 0

        if f.won.name.lower() == 'yes':
            status = 'Yes'
        elif f.won.name.lower() == 'no':
            status = 'No'
        else:
            status = 'NA'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                         forecast=f, total=total, start=start,
                         total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=status,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=0,
                         bet_against_user=0
                         ))
    print(data)
    return data


def forecast_result(request):

    forecast_live = ForeCast.objects.filter(status__name='Result Declared', private__name='No').order_by("-expire")

    return render(request, 'home/forecast_result.html',
                  {
                      "live": forecast_result_page(forecast_live),
                      "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                      "heading": "Results",
                      "title": "ForecastGuru",
                  })


def result_not_declared(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        forecast_result = Betting.objects.filter(users=profile, forecast__status__name='Result Declared').order_by("-forecast__expire")
        # forecast_closed = Betting.objects.filter(forecast__status__name='Closed', users=profile).order_by("forecast__expire")
        return render(request, 'home/forecast_result_pending.html',
                      {
                          "live": forecast_result_page_my(forecast_result),
                          # "closed": live_forecast_data(forecast_closed, profile),
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                          "heading": "My Results",
                          "title": "ForecastGuru",
                      })
    except Exception:

        return render(request, 'home/forecast_result_pending_no.html',
                      {
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                          "heading": "My Results",
                          "title": "ForecastGuru",
                      })


def forecast_result_page_my(forecast):
    data = []
    for f in forecast:
        forecast = f.forecast
        date = current.date()
        bet_start = forecast.expire.date()
        if date == bet_start:
            start = forecast.expire
            start = start.time()
            today = 'Yes'
        else:
            start = forecast.expire
            today = 'No'
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            total_wagered = betting_against + betting_for
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
            percent_against = (100 - percent_for)
            total = bet_against + bet_for
            bet_for_user = f.bet_for
            bet_against_user = f.bet_against
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_against = 0
            total = 0
            bet_for_user = 0
            bet_against_user = 0

        if forecast.won.name == 'Yes':
            status = 'Yes'
        elif forecast.won.name == 'No':
            status = 'No'
        else:
            status = 'NA'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                         forecast=forecast, total=total, start=start,
                         total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=status,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=bet_for_user,
                         bet_against_user=bet_against_user
                         ))
    return data


def get_ratio(bet_for, bet_against, total, status):
    ratio = 0
    if bet_against == 0 and bet_for == 0:
        ratio = "NA"
    elif bet_for == bet_against:
        ratio = 2
    elif status == 'Yes':
        try:
            if bet_against > 0:
                ratio = 1 + round((bet_against / bet_for), 2)
            else:
                ratio = 0
        except Exception:
            ratio = 1
    elif status == "No":
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
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
    except Exception:
        user = request.user.last_name
        return render(request, 'home/user_profile_nl.html', {
            "users": user,

        })
    date_joined = datetime.datetime.strftime(profile.created, '%b %d, %Y')

    total = profile.joining_points + profile.points_won_public + profile.points_won_private + profile.points_earned \
            - profile.points_lost_public - profile.points_lost_private
    totals = float(profile.successful_forecast + profile.unsuccessful_forecast)
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
    profile.market_fee_paid = (profile.points_won_private + profile.points_won_public) * 0.10
    profile.save()

    fore = ForeCast.objects.filter(user=profile).count()
    return render(request, 'home/user_profile.html', {
        "profile": profile,
        "date_joined": date_joined,
        "success": int(suc_per),
        "unsuccess": int(unsuc_per),
        "created": fore,
        "total": total,
        "status": predict_status(profile, suc_per),
        "balance": total,
        "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name,
        "won": profile.points_won_private + profile.points_won_public,
        "heading": "User Profile",
        "total_private": profile.joining_points + profile.points_earned + profile.points_won_private - profile.points_lost_private,
        "total_public": profile.points_won_public - profile.points_lost_public
    })


def predict_status(profile, suc_per):
    if profile.forecast_participated < 10 and suc_per < 50:
        status = "Beginner"
        return status
    elif profile.forecast_participated >= 10 and suc_per >= 50:
        status = "Expert"
        return status
    elif profile.forecast_participated >= 30 and suc_per >= 70:
        status = "INFLUENCER"
        return status
    elif profile.forecast_participated >= 50 and suc_per >= 90:
        status = "Guru"
        return status
    else:
        status = "Beginner"
        return status


def allocate_points(request):
    forecast = ForeCast.objects.filter(status__name='Closed', verified__name="Yes")
    status = Status.objects.get(name='Result Declared')
    for f in forecast:
        if f.won.name != "":
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
            if f.won.name == "Yes" and market_fee > bet_against:
                f.user.market_fee = bet_against * 0.05
                f.user.save()
                f.save()
            elif f.won.name == "No" and market_fee > bet_for:
                f.user.market_fee = bet_for * 0.05
                f.user.save()
                f.save()
            else:
                if bet_for == bet_against:
                    if f.won.name == "Yes":
                        ratio = 1
                        forecast_data(f, ratio, total, "Yes", bet_for)
                    else:
                        ratio = 1
                        forecast_data(f, ratio, total, "No", bet_against)
                elif bet_for > 0 and bet_against == 0 and f.won.name == 'Yes':
                    ratio = 1
                    forecast_data(f, ratio, total, "Yes", bet_for)
                elif bet_against > 0 and bet_for > 0 and f.won.name == 'Yes':
                    ratio = round(bet_against / bet_for, 2)
                    forecast_data(f, ratio, total, "Yes", bet_for)
                elif f.won.name == 'No' and bet_against == 0 and bet_for > 0:
                    ratio = 0
                    forecast_data(f, ratio, total, "No", bet_against)

                elif bet_against > 0 and bet_for == 0 and f.won.name== 'No':
                    ratio = 1
                    forecast_data(f, ratio, total, "No", bet_against)
                elif bet_for > 0 and f.won.name == 'No' and bet_against > 0:
                    ratio = round(bet_for / bet_against, 2)
                    forecast_data(f, ratio, total, "No", bet_against)
                elif f.won.name == 'Yes' and bet_for > 0 and bet_against == 0:
                    ratio = 0
                    forecast_data(f, ratio, total, "Yes", bet_for)
                elif bet_for == 0 and bet_against == 0:
                    f.won.name = "No Result."
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
        bet_for = b.bet_for
        bet_against = b.bet_against

        if bet_for == 0 and bet_against == 0:
            b.forecast.won.name = "NA"
            b.forecast.save()
            b.save()
        elif status == "Yes":
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

        elif status == "No":
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


def my_forecast(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        account = Authentication.objects.get(facebook_id=users.uid)
        forecast_live = Betting.objects.filter(forecast__status__name='Progress',
                                               users=account, forecast__private__name='No').order_by("forecast__expire")
        forecast_result = Betting.objects.filter(forecast__status__name='Result Declared', users=account,
                                                 forecast__private__name='No').order_by("forecast__expire")
        forecast_closed = Betting.objects.filter(forecast__status__name='Closed',
                                               users=account, forecast__private__name='No').order_by("forecast__expire")

        forecast_No_bet = ForeCast.objects.filter(user=account, private__name='No').order_by(
            "expire")
        not_bet = [f for f in forecast_No_bet if f.betting_set.all().count() == 0]
        if forecast_live.count() == 0 and forecast_result.count() == 0 and forecast_approval.count() == 0 and forecast_No_bet.count() == 0:
            return redirect("/trending/")
        else:
            return render(request, 'home/my_friend.html', {"live": live_forecast_data(forecast_live, account),
                                                  "result": forecast_result_data(forecast_result, account),
                                                  "forecast": live_forecast_data_bet(not_bet, account),
                                                  "closed": live_forecast_data(forecast_closed, account),
                                                  "heading": "My Forecast",
                                                  "title": "ForecastGuru",
                                                  "user": "Guest" if request.user.is_anonymous() else request.user.first_name})
    except Exception:
        return render(request, 'home/my_friend.html', {"heading": "My Forecast",
                                                     "title": "ForecastGuru",
                                                     "user": "Guest" if request.user.is_anonymous() else request.user.first_name})


def logout_view(request):
    logout(request)

    return redirect("/home/")


@csrf_exempt
def search_result(request):
    if request.method == "POST":

        query = request.POST.get('point', '')
        if query == "":
            return render(request, "home/search_data_nf.html", {"data": "No result found", "heading": "Search Forecast",
                                                           "title": "ForecastGuru",
                                                           "user": "Guest" if request.user.is_anonymous() else request.user.first_name})
        else:
            data = []

            forecast_live = ForeCast.objects.filter(heading__icontains=query, private__name='No',
                                                    status__name='Progress').order_by(
                "-expire")
            if len(forecast_live) == 0:
                return redirect("/trending/")
            else:
                for f in forecast_live:
                    date = current.date()

                    bet_start = (f.expire).date()

                    if date == bet_start:
                        start = f.expire
                        start = start.time()
                        today = 'Yes'
                    else:
                        start = f.expire

                        today = "No"
                    betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
                    betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
                    try:
                        total_wagered = betting_against + betting_for
                        bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
                        bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
                            'bet_against']
                        totl = float(bet_against + bet_for)
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
                return render(request, 'home/search_data.html',
                              {"live": data,
                               "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                               "heading": "Search Forecast",
                               "title": "ForecastGuru",
                               })
    else:
        return render(request, "home/search_data_nf.html", {"data": "No result found", "heading": "Search Forecast",
                                                       "title": "ForecastGuru",
                                                       "user": "Guest" if request.user.is_anonymous() else request.user.first_name})


def live_forecast_data_bet(forecast_live, account):
    data = []

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = forecast.expire.date()

        if date == bet_start:
            start = f.expire
            start = start.time()
            today = 'Yes'
        else:
            start = f.expire

            today = "No"
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
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
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
            start = forecast.expire
            start = start.time()
            today = 'Yes'
        else:
            start = forecast.expire
            today = "No"
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
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
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
        forecast = f.forecast
        bet_start = forecast.expire.date()

        if date == bet_start:
            start = forecast.expire
            start = start.time()
            today = 'Yes'
        else:
            start = forecast.expire
            today = "No"
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
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
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
            start = forecast.expire
            start = start.time()
            today = 'Yes'
        else:
            start = forecast.expire
            today = 'No'
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
        try:
            if forecast.won.name == 'Yes':
                status = 'Yes'
            elif forecast.won.name == 'No':
                status = 'No'
        except Exception:
            status = 'NA'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=status,  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         bet_against_user=bet_against_user if bet_against_user else 0
                         ))

    return data


def forecast_result_data(forecast_live, account):
    data = []
    for f in forecast_live:
        forecast = f.forecast
        date = current.date()
        bet_start = forecast.expire.date()
        if date == bet_start:
            start = forecast.expire
            start = start.time()
            today = 'Yes'
        else:
            start = forecast.expire
            today = 'No'
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
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
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
        try:
            if forecast.won.name == 'Yes':
                status = 'Yes'
            elif forecast.won.name == 'No':
                status = 'No'
        except Exception:
            status = 'NA'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=status,  # waggered=waggered,
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
            start = forecast.expire
            start = start.time()
            today = 'Yes'
        else:
            start = forecast.expire
            today = 'No'
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
            totl = float(bet_against + bet_for)
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

        if forecast.won.name == 'Yes':
            status = 'Yes'
        elif forecast.won.name == 'No':
            status = 'No'
        else:
            status = 'NA'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=status,  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against,
                         bet_for=bet_for,
                         bet_for_user=bet_for_user if bet_for_user else 0,
                         bet_against_user=bet_against_user if bet_against_user else 0
                         ))

    return data


def my_forecast_private(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        account = Authentication.objects.get(facebook_id=users.uid)
        forecast_live = ForeCast.objects.filter(status__name='Progress', user=account,
                                                private__name='Yes').order_by("expire")

        forecast_result = ForeCast.objects.filter(status__name='Result Declared',user=account, private__name='Yes').order_by("expire")
        # forecast_approval = InviteFriends.objects.filter(user=account).exclude(forecast__in=forecast_result).exclude(forecast__in=forecast_live).order_by("-forecast__expire")
        return render(request, 'home/my_friend_private.html',
                      {
                          "live": live_forecast_data_private(forecast_live, account),
                          "result": forecast_result_data_private(forecast_result, account),
                          # "approval": forecast_invite_data(forecast_approval, account),
                          # "approval": forecast_result_data_private(forecast_result, account),
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                          "heading": "Forecast Private",
                          "title": "ForecastGuru",
                      })
    except Exception:
        return render(request, 'home/my_friend_nl.html',
                      {"user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                       "heading": "Forecast Private",
                       "title": "ForecastGuru",
                       })


def e_handler404(request):
    context = RequestContext(request)
    response = render_to_response('home/404.html', context)
    response.status_code = 404
    return response


def e_handler500(request):
    context = RequestContext(request)
    response = render_to_response('home/500.html', context)
    response.status_code = 500
    return response


def update_close_status(request):
    now = datetime.datetime.now()
    status = Status.objects.get(name='Closed')
    ForeCast.objects.filter(expire__lte=now, status__name='Progress').update(status=status)
    return HttpResponse("updated")


def privacy(request):
    return render(request, 'home/privacy_policy.html',
                  {
                      "heading": "Privacy Policy",
                      "title": "ForecastGuru",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name

                  })


def terms(request):
    return render(request, 'home/terms.html',
                  {
                      "heading": "Terms and Conditions",
                      "title": "ForecastGuru",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name

    })


def faq(request):
    return render(request, 'home/faq.html',
                  {
                      "heading": "Frequently Asked Questions",
                      "title": "ForecastGuru",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name
    })


@staff_member_required
@csrf_exempt
def import_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES["csv_file"]
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'File is not CSV type')
            return redirect("/import_csv/")
        # if file is too large, return
        if csv_file.multiple_chunks():
            messages.error(request, "Uploaded file is too big (%.2f MB)." % (csv_file.size / (1000 * 1000),))
            return redirect("/import_csv/")

        file_data = csv_file.read().decode("utf-8")

        lines = file_data.split("\n")
        # loop over the lines and save them in db. If error , store as string and then display
        for i in range(len(lines) - 1):
            fields = lines[i].split(",")
            try:
                private = Private.objects.get(name='No')
            except Exception:
                return HttpResponse("Error - In Private field")
            try:
                status = Status.objects.get(name='Progress')
            except Exception:
                return HttpResponse("Error - In Status field")
            try:
                verified = Verified.objects.get(name='No')
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
                social = Authentication.objects.get(facebook_id=user)
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
                Yes = randrange(1000, 9000, 1000)
                No = randrange(1000, 9000, 1000)
                admin = Authentication.objects.get(facebook_id__username="admin")
                Betting.objects.create(forecast=f, users=admin, bet_for=Yes, bet_against=No)

        return HttpResponse(json.dumps(dict(message="File Uploaded Successful")))
    else:
        return render(request, 'home/import_csv.html',
                      {
                          "heading": "Import CSV",
                          "title": "ForecastGuru",
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name
                      })


def thank_you(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        status = LoginStatus.objects.get(user=profile)
        if status.status == 1:
            return redirect("/extra/")
        else:
            status.status = 1
            status.save()
            return render(request, "home/thank_you.html",
                          {
                              "heading": "Registration Complete",
                              "title": "ForecastGuru",
                              "user": "Guest" if request.user.is_anonymous() else request.user.first_name
                          })
    except Exception:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        LoginStatus.objects.create(user=profile, status=1)

        return render(request, "home/thank_you.html",
                      {
                          "heading": "Registration Complete",
                          "title": "ForecastGuru",
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name
                      })


def trending_forecast(request):
    current = datetime.datetime.now().date().strftime("%Y-%m-%d")
    forecast = ForeCast.objects.filter(expire__gte=current + " 00:00:00", status__name='Progress',private__name='No',).order_by('expire')
    data = []
    for f in forecast:
        bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
        bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))[
            'bet_against']
        if bet_for == None and bet_against == None:
            pass
        else:
            if bet_for + bet_against > 15000:
                data.append(f)

    if len(data) == 0:
        return render(request, 'home/trending_no.html',
                      {
                          "heading": "Trending Forecast",
                          "title": "ForecastGuru",
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name
                      })
    else:

        objects = data[:10]

        return render(request, 'home/trending.html',
                      {
                          "live": trending_data(objects),
                          "heading": "Trending Forecast",
                          "title": "ForecastGuru",
                          "user": "Guest" if request.user.is_anonymous() else request.user.first_name
                      })


def trending_data(objects):
    data_all = []
    for f in objects:
        date = datetime.datetime.now().date()
        forecast = f
        bet_start = forecast.expire.date()
        if date == bet_start:
            start = forecast.expire
            start = start.time()
            today = 'yes'
        else:
            start = forecast.expire

            today = 'no'
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
        data_all.append(
            dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                 total=total, start=start, total_user=betting_for + betting_against,
                 betting_for=betting_for, betting_against=betting_against, today=today,
                 participants=total_wagered, bet_for=bet_for,
                 bet_against=bet_against,
                 bet_for_user=0,
                 bet_against_user=0))
    return data_all


@csrf_exempt
def search_result(request):
    if request.method == "POST":

        query = request.POST.get('point', '')
        if query == "":
            return render(request, "home/search_data_nf.html", {
                "data": "No result found", "heading": "Search Forecast",
                "title": "ForecastGuru",
                "user": "Guest" if request.user.is_anonymous() else request.user.username})
        else:
            data = []

            forecast_live = ForeCast.objects.filter(heading__icontains=query,
                                                    status__name='Progress').order_by("-expire")
            if len(forecast_live) == 0:
                return redirect("/trending/")
            else:
                for f in forecast_live:
                    date = current.date()

                    bet_start = f.expire.date()

                    if date == bet_start:
                        start = f.expire
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
                        totl = float(bet_against + bet_for)
                        percent_for = (float(bet_for) / totl) * 100
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
                return render(request, 'home/search_data.html',
                              {"live": data,
                               "user": "Guest" if request.user.is_anonymous() else request.user.first_name,
                               "heading": "Search Forecast",
                               "title": "ForecastGuru",
                               })
    else:
        return render(request, "home/search_data_nf.html", {"data": "No result found", "heading": "Search Forecast",
                                                       "title": "ForecastGuru",
                                                       "user": "Guest" if request.user.is_anonymous() else request.user.first_name})


def refer_earn(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
    except Exception:
        profile =[]
    return render(request, "home/refer_earn.html",
                  {
                      "heading": "Refer And Earn",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name,
                      "profile": profile,
                  })


def earn_points(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
    except Exception:
        profile =[]
    return render(request, "home/earn_points.html",
                  {
                      "heading": "Earn Points",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name,
                      "profile": profile,
                  })


def redeem_points(request):
    try:
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
    except Exception:
        profile =[]
    redeem = RedeemPoints.objects.latest('id')
    return render(request, "home/redeem.html",
                  {
                      "heading": "Redeem Points",
                      "first_name": "Guest" if request.user.is_anonymous() else request.user.first_name,
                      "profile": profile,
                      "redeem_from": redeem.redeem_points,
                      "redeem_to": redeem.redeem_to,
                  })


def category(request):
    category = Category.objects.all().order_by('identifier')
    data = []
    for c in category:
        image = c.subcategory_set.get(name='Others').image

        data.append(dict(name=c.name, id=c.id, image=image))
    return render(request, 'home/category.html', {'category': data,
                                             "heading": "Categories",
                                             "title": "ForecastGuru",
                                             "user": "Guest" if request.user.is_anonymous() else request.user.username})


def category_search(request, userid):
    category_id = Category.objects.get(id=userid)
    sub = SubCategory.objects.filter(category=category_id).order_by('identifier')
    # try:
    acc = SocialAccount.objects.get(user=request.user)
    profile = Authentication.objects.get(facebook_id=acc.uid)
    if len(forecast_live_view(category_id, profile)) == 0:
        return HttpResponseRedirect("/trending/")
    else:
        return render(request, 'home/category_search.html',
                      {
                          "live": forecast_live_view(category_id, profile),
                          "heading": category_id.name, "sub": sub,
                          "title": "ForecastGuru", 'category_id': category_id.id,
                          "user": "Guest" if request.user.is_anonymous() else request.user.username
                      })

    # except Exception:
    #
    #     return render(request, 'home/category_search.html',
    #                   {
    #                       "live": forecast_live_view_bt(category_id),
    #                       "heading": category_id.name, "sub": sub,
    #                       "title": "ForecastGuru", 'category_id': category_id.id,
    #                       "user": "Guest" if request.user.is_anonymous() else request.user.username
    #                   })


def sub_category_data(request, userid):
    subcategory = SubCategory.objects.get(id=userid)
    sub = SubCategory.objects.filter(category=subcategory.category).order_by('identifier')
    category = Category.objects.get(id=subcategory.category.id)
    # try:

    acc = SocialAccount.objects.get(user=request.user)
    profile = Authentication.objects.get(facebook_id=acc.uid)
    if len(forecast_live_view_sub(subcategory, profile)) == 0:
        return HttpResponseRedirect("/trending/")
    else:
        return render(request, 'home/category_search.html',
                      {
                          "live": forecast_live_view_sub(subcategory, profile),
                          "heading": subcategory.name, "sub": sub,
                          "title": "ForecastGuru", "category_id": category.id,
                          "user": "Guest" if request.user.is_anonymous() else request.user.username
                      })

    # except Exception:
    #
    #     return render(request, 'home/category_search.html',
    #                   {
    #                       "live": forecast_live_view_bt_sub(subcategory),
    #                       "heading": subcategory.name, "sub": sub,
    #                       "title": "ForecastGuru", "category_id": category.id,
    #                       "user": "Guest" if request.user.is_anonymous() else request.user.username
    #                   })


def forecast_live_view_sub(category, profile):
    data = []
    forecast_live = ForeCast.objects.filter(approved__name="yes", private__name='no', sub_category=category,
                                            status__name='In-Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = forecast.expire  + datetime.timedelta(hours=5, minutes=30)
            start = start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = forecast.expire
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
    forecast_live = ForeCast.objects.filter(private__name='No', category=category_id,
                                            status__name='Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = f.expire  + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = f.expire

            today = "no"
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))[
                'bet_against']
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
            percent_against = (100 - percent_for)
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
    forecast_live = ForeCast.objects.filter(private__name='No', sub_category=category_id,
                                            status__name='Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = forecast.expire  + datetime.timedelta(hours=5, minutes=30)
            start = start.time().strftime("%I:%M:%S")
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
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
            percent_against = (100 - percent_for)
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


def forecast_live_view(category, profile):
    data = []
    forecast_live = ForeCast.objects.filter(private__name='No', category=category,
                                            status__name='Progress').order_by("expire")

    for f in forecast_live:
        date = current.date()
        forecast = f
        bet_start = (forecast.expire).date()

        if date == bet_start:
            start = f.expire  + datetime.timedelta(hours=5, minutes=30)
            start = start.time()
            today = 'yes'
        else:
            start = f.expire

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
            totl = float(bet_against + bet_for)
            percent_for = (float(bet_for) / totl) * 100
            percent_against = (100 - percent_for)
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


@csrf_exempt
def payment(request):
    if request.method == "POST":
        order_id = Checksum.__id_generator__()
        cust_id = "payment_maker@email.com"
        data_dict = {
                    'ORDER_ID':order_id,
                    'TXN_AMOUNT': request.POST.get('to_point', 0),
                    'CUST_ID': cust_id
                }
        return HttpResponse(PaytmPaymentPage(data_dict))
        # return render(request, "payment.html")
    else:
        return render(request, 'home/payments.html')


@csrf_exempt
def response(request):
    resp = VerifyPaytmResponse(request)
    if resp['verified']:
        # save success details to db
        print(resp['paytm']['ORDERID'])  #SAVE THIS ORDER ID TO DB FOR TRANSACTION HISTORY
        return JsonResponse(resp['paytm'])
    else:
        return HttpResponse("Verification Failed")


def test_notif(request):
    # data = [dict(title='ForecastGuru', body='INDIA TOUR OF IRELAND AND ENGLAND 2018.03:30PM 4th Test,IND vs ENG at Southampton, Aug 30-Sep 3.INDIA will win.',forward='https://forecast.guru/forecast/925/'),
    #         dict(title='ForecastGuru', body='INDIA TOUR OF IRELAND AND ENGLAND 201803:30 PM 5th Test, IND vs ENG at London, Sep 7-11 2018.INDIA will win.', forward='https://forecast.guru/forecast/926/')]
    data = [dict(body=s.body, url=s.url) for s in SendNotification.objects.filter(status=0)]
    SendNotification.objects.filter(status=0).update(status=1)
    return HttpResponse(json.dumps(data))


def notification(request):
    users = SocialAccount.objects.get(user=request.user)
    profile = Authentication.objects.get(facebook_id=users.uid)
    notification = UserNotifications.objects.filter(user=profile)
    return render(request, "home/notification.html", {"notification": notification,
                                                      "heading": "Notification"})


@csrf_exempt
def save_user_id(request):
    if request.method == "POST":
        sub_id = request.POST.get('sub_id', '')
        users = SocialAccount.objects.get(user=request.user)
        profile = Authentication.objects.get(facebook_id=users.uid)
        if sub_id == 'false':
            return HttpResponse(json.dumps(dict(message='fail')))
        try:
            n = NotificationUser.objects.get(user=profile, subscriber_id=sub_id)
        except Exception:
            NotificationUser.objects.create(user=profile, subscriber_id=sub_id)
        return HttpResponse(json.dumps(dict(message='success')))


def send_notification(text, message, url, subscriber_id, user):
    headers = {
        'Authorization': 'key=e5e48625ab5bc843ae9e215841414093',
    }
    data = [
        ('title', text),
        ('message', message),
        ('url', url),
        ('subscriber_id', str(subscriber_id)),

    ]
    response = requests.post('https://pushcrew.com/api/v1/send/individual', headers=headers, data=data)
    NotificationPanel.objects.create(title=text, message=message, url=url, status=1, user=user)
    return response.status_code


def send_notification_user(request):
    notification = NotificationPanel.objects.filter(status=0)
    headers = {
        'Authorization': 'key=e5e48625ab5bc843ae9e215841414093',
    }

    for n in notification:
        n.status = 1
        n.save()
        sub_id = NotificationUser.objects.filter(user=n.user)
        if len(sub_id) > 0:
            for s in sub_id:
                data = [
                    ('title', n.title),
                    ('message', n.message),
                    ('url', n.url),
                    ('subscriber_id', str(s.subscriber_id)),

                ]
                response = requests.post('https://pushcrew.com/api/v1/send/individual', headers=headers, data=data)
    return HttpResponse("updated")


def send_notification_all(request):
    notification = SendNotificationAll.objects.filter(status=0)
    headers = {
        'Authorization': 'key=e5e48625ab5bc843ae9e215841414093',
    }

    for f in notification:
        f.status = 1
        f.save()
        data = [
            ('title', str(f.title)),
            ('message', str(f.message)),
            ('url', f.url),
        ]
        response = requests.post('https://pushcrew.com/api/v1/send/all', headers=headers, data=data)
    return HttpResponse("updated")


def private_subscribe(request):
    forecast = ForeCast.objects.filter(status__name = 'Closed', private__name = 'yes')
    for f in forecast:
        if f.private.name == 'yes':
            try:
                sub_id = f.user.notificationuser_set.all()
                if len(sub_id) > 0:
                    for i in sub_id:
                        send_notification("Forecast Guru", "Hello " + str(f.user.user.username) + ". Please declare result for the forecast " + str(f.heading),
                                      "https://forecast.guru/forecast/{}/".format(f.id), str(i.subscriber_id), f.user)
            except Exception:
                pass
    return HttpResponse("updated")


def main_login(request):
    j = JoiningPoints.objects.latest('id').points
    return render(request, "home/login_main.html",{"points": j})


@csrf_exempt
def login_facebook(request):
    if request.method == "POST":
        userID = request.POST.get('facebook_id', "")
        first_name = request.POST.get('first_name', "")
        last_name = request.POST.get('last_name', "")
        email = request.POST.get('email', "")
        if not userID:
            return HttpResponse(json.dumps(dict(status=400, message='Facebook ID missing')))
        try:
            user = User.objects.get(username=userID)
            auth = authenticate(request, username=userID, password=userID)

            if auth:
                login(request, auth)
                return HttpResponse(json.dumps(dict(status=200, message='Login Success')))
            else:
                return HttpResponse(json.dumps(dict(status=400, message='Login Fail')))
        except Exception:
            user = User.objects.create(username=userID,
                                       email=email,
                                       first_name=first_name,
                                       last_name=last_name
                                       )
            fuser = Authentication.objects.create(facebook_id=userID,
                                                  first_name=first_name,
                                                  last_name=last_name,
                                                  email=email
                                                  )
            fuser.referral_code = id_generator(first_name, last_name)
            fuser.points_earned = JoiningPoints.objects.latest('id').points
            fuser.save()
            user.set_password(userID)
            user.save()
            auth = authenticate(request, username=userID, password=userID)
            if auth:
                login(request, auth)
                return HttpResponse(json.dumps(dict(status=200, message='User Registered', url="https://fstage.sirez.com/referral_code/")))
            else:
                return HttpResponse(json.dumps(dict(status=400, message='SignUp Fail')))
    else:
        return HttpResponse(json.dumps(dict(status=400, message='Only Post Request')))