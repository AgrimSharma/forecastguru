# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import json
from django.shortcuts import render, HttpResponse, HttpResponseRedirect, render_to_response
from django.views.decorators.csrf import csrf_exempt
from .models import *
from django.db.models import Sum
import datetime
from payu_biz.views import make_transaction
from uuid import uuid4
from django.conf import settings
from django.contrib.auth import logout, login, authenticate
from django.contrib.auth.models import User
import random


current = datetime.datetime.now()


def test(request):
    return render(request, 'main.html')


@csrf_exempt
def create_forecast(request):
    if request.method == 'POST':
        try:
            user = request.POST.get('user', '')
            category = request.POST.get('categories', '')
            sub_category = request.POST.get('subcategories', '')
            heading = request.POST.get('heading', '')
            # source = request.POST.get('source', '')
            expire = request.POST.get('expire', '')
            start = request.POST.get('start', '')
            cat = Category.objects.get(id=category)
            sub_cat = SubCategory.objects.get(id=sub_category)
            # user = User.objects.get(username=user)
            try:
                users = SocialAccount.objects.get(user=request.user)
            except Exception:
                return HttpResponseRedirect("/home/")
            status = Status.objects.get(name='In-Progress')
            f = ForeCast.objects.create(category=cat, sub_category=sub_cat,
                                        user=users, heading=heading,
                                        expire=datetime.datetime.strptime(expire, "%Y-%m-%d %H:%M"),
                                        start=datetime.datetime.strptime(start, "%Y-%m-%d %H:%M"), approved=False,
                                        status=status, created=current, private=False,
                                        )
            f.save()
            return HttpResponseRedirect("/live_forecast/")
        except Exception:

            return HttpResponse(json.dumps(dict(status=400, message='Try again later')))

    else:
        category = Category.objects.all().order_by('name')
        return render(request, 'create_forecast.html', {'category':category,

                                                        "user": request.user.username
                                                        })


def closing_soon(request):
    forecast = ForeCast.objects.filter(start__lte=current, approved=True, status__name='Closing Soon').order_by("-created")
    return render(request, 'closing_soon.html',{"forecast":forecast})


def live_forecast(request):
    data = []

    forecast_live = ForeCast.objects.filter(approved=True, status__name='In-Progress').order_by("-expire")
    for f in forecast_live:
        date = current.date()

        bet_start = f.expire.date()

        if date == bet_start:
            start = f.expire
            start = start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = f.expire

            today = "no"
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))['bet_against']
            totl = bet_against+ bet_for
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
    return render(request, 'live_forecast.html', {"live": data})


def forecast_result(request):
    data = []
    banner = Banner.objects.all()
    forecast_live = ForeCast.objects.filter(approved=True, status__name='Closed').order_by("-created")
    for f in forecast_live:
        date = current.date()
        bet_start = f.start.date()
        if date == bet_start:
            start = f.expire.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = f.expire
            today = 'no'
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))['bet_against']
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
        if f.won == 'bet_for':
            won="Yes"
            # waggered = bet_for
            try:
                if betting_against > 0:
                    ratio = 1 + round((bet_for / total),2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        else:
            won="No"
            # waggered = bet_against
            try:
                if betting_for> 0:
                    ratio = 1 + round((bet_against / total),2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                         forecast=f, total=total, start=start,
                         total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered,won=won, ratio=ratio,
                         bet_against=bet_against, bet_for=bet_for))

    return render(request, 'forecast_result.html', {"live": data, 'banner': banner})


def profile(request):
    try:
        user = request.user
        # users = User.objects.get(username=user.username)
        profile = SocialAccount.objects.get(user=user)
    except Exception:
        user = request.user
        # users = User.objects.get(username=user.username)
        # profile = SocialAccount.objects.get(user=user)
        return render(request, 'user_profile_nl.html', {
            "users": user.username,

        })
    date_joined = datetime.datetime.strftime(profile.date_joined, '%b %d, %Y')
    total = profile.successful_forecast + profile.unsuccessful_forecast
    try:
        bet_for = Betting.objects.filter(users=profile).aggregate(bet_for=Sum('bet_for'))['bet_for']
        bet_against = Betting.objects.filter(users=profile).aggregate(bet_against=Sum('bet_against'))['bet_against']
        point = bet_against + bet_for
    except Exception:
        bet_for = 0
        bet_against = 0
        point = 0
    try:
        suc_per = (profile.successful_forecast / total) * 100
        unsuc_per = 100 - (profile.successful_forecast / total) * 100
    except Exception:
        suc_per = 0
        unsuc_per = 0

    if profile.fg_points_total == 0:
        profile.fg_points_total = profile.fg_points_free + profile.fg_points_bought + profile.fg_points_won
        profile.save()
    if 0 < profile.forecast_participated < 25:
        status = "Beginner"
    elif 25 <= profile.forecast_participated < 75:
        status = "Intermediate"
    elif profile.forecast_participated > 75:
        status = "Guru"
    return render(request, 'user_profile.html', {"profile": profile,
                                                 "date_joined":date_joined,
                                                 "success":int(suc_per),
                                                 "unsuccess": int(unsuc_per),
                                                 "user": request.user.username,
                                                 "point": point,
                                                 "total": total,
                                                 "status": "Beginner" if 0 <= profile.forecast_participated < 25 else "Intermediate"
                                                 })


def betting(request, userid):
    forecast = ForeCast.objects.get(id=userid)
    try:
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        betting_sum = Betting.objects.filter(forecast=forecast).aggregate(
            bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
        try:
            total_wagered = betting_sum['bet_for'] + betting_sum['bet_against']
        except Exception:
            total_wagered = 0
        end_date = datetime.datetime.strftime(forecast.expire, '%b %d, %Y')
        end_time = datetime.datetime.strftime(forecast.expire, '%H:%M')
        try:
            percent = (betting_for / (betting_for + betting_against)) *100
        except Exception:
            percent = 0

        if forecast.status.name == 'In-Progress':
            status = 'Currently LIVE'
        elif forecast.status.name == 'Closed':
            status = 'Currently CLOSED'
        else:
            status = 'Waiting'
        success = SocialAccount.objects.get(user__username=request.user)
        print(success)
        return render(request, 'betting.html', {'forecast': forecast, 'betting':betting,
                                                'bet_for': betting_for if betting_for else 0,
                                                'against':betting_against if betting_against else 0,
                                                'total': total_wagered if total_wagered else 0,
                                                "end_date":end_date, "end_time":end_time,
                                                'status':status, "percent": percent,
                                                "success": success.successful_forecast,
                                                "user": request.user.username,
                                                "sums": betting_against + betting_for
                                                })
    except Exception:
        return render(request, 'betting.html', {'forecast': forecast,"user": request.user.username})


@csrf_exempt
def bet_post(request):
    if request.method == 'POST':
        try:
            user = request.user
            account=SocialAccount.objects.get(user=user)
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
                    if b.bet_for < points:
                        b.bet_for = points
                        b.users.fg_points_total = b.users.fg_points_total - points
                        b.users.save()
                        b.save()
                    else:
                        return HttpResponse(json.dumps(dict(message="FG point for forecast should be greater than previous {}".format(b.bet_for))))
                else:
                    if b.bet_against < points:
                        b.bet_against = b.bet_against + points
                        b.users.fg_points_total = b.users.fg_points_total - points
                        b.users.save()
                        b.save()
                    else:
                        return HttpResponse(json.dumps(
                            dict(message="FG point for forecast should be greater than previous {}".format(b.bet_against))))
            except Exception:
                if vote == 'email':
                    b = Betting.objects.create(forecast=forecasts, users=account, bet_for=points, bet_against=0)
                    b.users.fg_points_total = b.users.fg_points_total - points
                    b.users.save()
                    b.save()
                else:
                    b = Betting.objects.create(forecast=forecasts, users=account, bet_for=0, bet_against=points)
                    b.users.fg_points_total = b.users.fg_points_total - points
                    b.users.save()
                    b.save()
            return HttpResponse(json.dumps(dict(message='success')))
        else:
            return HttpResponse(json.dumps(dict(message='balance')))
        # except Exception:
            # return HttpResponse(json.dumps(dict(message='success')))
    else:
        return HttpResponse(json.dumps(dict(message='Please use POST')))


def allocate_points(request):

    current = datetime.datetime.now()
    current_new = datetime.datetime.strftime(current, "%m/%d/%Y %I:%M %p")
    current_n = datetime.datetime.strptime(current_new, "%m/%d/%Y %I:%M %p")
    expired = current - datetime.timedelta(hours=2)
    forecast = ForeCast.objects.filter(expire__gte=expired, expire__lte=current_n, status__name='Closed')
    for f in forecast:
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

        betting_sum = Betting.objects.filter(forecast=f).aggregate(
            bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
        total_wagered = betting_sum['bet_for'] + betting_sum['bet_against']
        bet_for = betting_sum['bet_for']
        bet_against = betting_sum['bet_against']
        total = total_wagered - total_wagered * (f.market_fee/100)
        if betting_against == 0 or betting_for == 0:
            return " Can't process as Bet For OR Bet Against Can't be 0"
        elif f.won == 'bet_for':
            if betting_for > betting_against:
                forecast_data(f, total, bet_for, 'bet_for')
            elif betting_against > bet_for:
                forecast_data(f, total, bet_for, 'bet_for')
            else:
                forecast_data(f, total, bet_for, 'bet_for')

        elif f.won == 'bet_against':
            if betting_for > betting_against:
                forecast_data(f, total, bet_against, 'bet_against')
            elif betting_against > bet_for:
                forecast_data(f, total, bet_against, 'bet_against')
            else:
                forecast_data(f, total, bet_against, 'bet_against')
    return HttpResponse('Success')


def forecast_data(forecast, total_left, bet, bet_type):
    bets_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0)
    bets_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0)
    if bet_type == 'bet_for':

        for b in bets_for:
            left = total_left - b.bet_for

            b.users.fg_points_won = abs(b.users.fg_points_won + (b.bet_for * (b.bet_for/left)))
            if b.users.fg_points_total > 0:
                b.users.fg_points_total = b.users.fg_points_won + b.users.fg_points_bought + b.users.fg_points_total
            else:
                b.users.fg_points_total = b.users.fg_points_won + b.users.fg_points_bought + b.users.fg_points_free
            b.users.successful_forecast = b.users.successful_forecast + 1
            b.users.forecast_participated = b.users.forecast_participated + 1
            b.users.save()
            b.save()
        for bf in bets_against:
            bf.users.fg_points_lost = abs(bf.users.fg_points_lost + bf.bet_against)
            if bf.users.fg_points_total > 0:
                bf.users.fg_points_total = - bf.users.fg_points_lost + bf.users.fg_points_bought + bf.users.fg_points_total
            else:
                bf.users.fg_points_total = - bf.users.fg_points_lost + bf.users.fg_points_bought + bf.users.fg_points_free
            bf.users.unsuccessful_forecast = bf.users.unsuccessful_forecast + 1
            bf.users.forecast_participated = bf.users.forecast_participated + 1
            bf.users.save()
            bf.save()
    else:

        for bf in bets_for:
            bf.users.fg_points_lost = abs(bf.users.fg_points_lost + bf.bet_for)
            if bf.users.fg_points_total > 0:
                bf.users.fg_points_total = bf.users.fg_points_bought - bf.users.fg_points_lost + bf.users.fg_points_total
            else:
                bf.users.fg_points_total = bf.users.fg_points_bought - bf.users.fg_points_lost + bf.users.fg_points_free
            bf.users.unsuccessful_forecast = bf.users.unsuccessful_forecast + 1
            bf.users.forecast_participated = bf.users.forecast_participated + 1
            bf.users.save()
            bf.save()
        for ba in bets_against:
            left = total_left - ba.bet_against
            ba.users.fg_points_won = abs(ba.users.fg_points_won + (ba.bet_against * (ba.bet_against/left)))
            if ba.users.fg_points_total > 0:
                ba.users.fg_points_total = ba.users.fg_points_won + ba.users.fg_points_bought + ba.users.fg_points_total
            else:
                ba.users.fg_points_total = ba.users.fg_points_won + ba.users.fg_points_bought + ba.users.fg_points_free
            ba.users.successful_forecast = ba.users.successful_forecast + 1
            ba.users.forecast_participated = ba.users.forecast_participated + 1
            ba.users.save()
            ba.save()


### PayuMoney


@csrf_exempt
def home(request):
    if request.method == "POST":
        amount = request.POST.get('button1',0)
        account = SocialAccount.objects.get(user=request.user)
        """ DO your stuffs here and create a dictionary (key,value pair) """
        cleaned_data = {
            "key": settings.MERCHANT_KEY, "salt": settings.MERCHANT_SALT,
            'txnid': uuid4(), 'amount': int(amount), 'productinfo': "sample_produ",
            'firstname':account.user.username, 'email': "agrim.sharma@sirez.com", 'udf1': '',
            'udf2': '', 'udf3': '', 'udf4': '', 'udf5': '', 'udf6': '', 'udf7': '',
            'udf8': '', 'udf9': '', 'udf10': '','phone':"8800673006"
            }
        """ Payment gate calling with provided data dict """
        return HttpResponse(make_transaction(cleaned_data))


def payment(request):
    return render(request, "payumoney.html", {"user": request.user.username})


@csrf_exempt
def payu_success(request):
    """ we are in the payu success mode"""
    account = SocialAccount.objects.get(user=request.user)

    data = json.loads(json.dumps(request.POST))
    Order.objects.create(user=account, order_date=current, txnid=data['txnid'], amount=data['net_amount_debit'])
    print(data)
    amount = data['net_amount_debit']
    if amount == "49":
        account.fg_points_bought = account.fg_points_bought + 5000
    elif amount == "99":
        account.fg_points_bought = account.fg_points_bought + 10000
    elif amount == "499":
        account.fg_points_bought = account.fg_points_bought + 60000
    elif amount == "999":
        account.fg_points_bought = account.fg_points_bought + 150000
    elif amount == "3999":
        account.fg_points_bought = account.fg_points_bought + 1000000

    account.save()
    return HttpResponseRedirect("/accounts/profile/")


@csrf_exempt
def payu_failure(request):
    """ We are in payu failure mode"""
    return HttpResponseRedirect("/profile/")


@csrf_exempt
def payu_cancel(request):
    """ We are in the Payu cancel mode"""
    return HttpResponseRedirect("/profile/")


def category(request):
    category = Category.objects.all().order_by('name')
    return render(request, 'category.html',{'category': category, "user": request.user.username})


def category_search(request, userid):
    category = Category.objects.get(id=userid)

    return render(request, 'category_search.html',
                  {
                      "live": forecast_live_view(category),
                      "result": forecast_result_view(category),
                      "user": request.user.username
                  })


def my_forecast(request):
    try:
        user = request.user.id
        users = User.objects.get(id=user)
        account = SocialAccount.objects.get(user=users)
        forecast_live = Betting.objects.filter(forecast__approved=True, forecast__status__name='In-Progress', users=account).order_by(
            "forecast__expire")
    # return HttpResponse(live_forecast_data(forecast_live))

        forecast_result = Betting.objects.filter(forecast__approved=True, forecast__status__name='Closed', users=account).order_by("forecast__expire")

        return render(request, 'my_friend.html', {"live": live_forecast_data(forecast_live),
                                                  "result": forecast_result_data(forecast_result),
                                                  "user": request.user.username})

    except Exception:
        return render(request, 'my_friend_nl.html', {"user": request.user.username})



def logout_view(request):
    logout(request)
    return HttpResponseRedirect("/home/")


def blank_page(request):
    return render(request, 'test.html', {})


@csrf_exempt
def search_result(request):
    if request.method == "POST":

        query = request.POST.get('point','')
        if query == "":
            return render(request, "search_data.html", {"data": "No result found"})
        else:
            data = []
            forecast_live = ForeCast.objects.filter(heading__icontains=query).order_by("-created")
            for f in forecast_live:
                date = current.date()
                bet_start = f.start.date()
                if date == bet_start:
                    start = f.start.time().strftime("%I:%M:%S")
                else:
                    start = f.start
                betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
                betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
                try:

                    total_wagered = betting_against + betting_for
                    percent_for = (betting_for / total_wagered) * 100
                    percent_against = (1 - (betting_for / total_wagered)) * 100

                except Exception:
                    total_wagered = 0
                    percent_for = 0
                    percent_against = 0

                betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
                betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
                data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=f,
                                 total=betting_against + betting_for, start=start))
            return render(request, 'search_data.html',
                          {"live": data, "user": request.user.username})
    else:
        return HttpResponseRedirect("/live_forecast/")


@csrf_exempt
def signup_page(request):
    if request.method == 'POST':

        username = request.POST.get('username','')
        password = request.POST.get('password','')
        email = request.POST.get('email','')
        if not username or not password or not email:
            return HttpResponse(json.dumps(dict("Please fill all details")))
        else:
            try:
                user = User.objects.get(email=email)
                return HttpResponse(json.dumps(dict(message="User Already exists")))
            except Exception:
                user = User.objects.create(email=email, username=username)
                user.set_password(password)
                sa = SocialAccount.objects.create(user=user, uid=random.randint(1000, 100000),)
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
        forecast = ForeCast.objects.get(id=request.POST.get('id',''))
        return render_to_response('forecast_modal.html',
                                  {'forecast': forecast}, )
    else:
        return HttpResponse(json.dumps(dict(error="Try again later")))


def live_forecast_data(forecast_live):
    data = []

    for f in forecast_live:
        date = current.date()
        forecast = f.forecast
        bet_start = (forecast.expire + datetime.timedelta(hours=5, minutes=30)).date()

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
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))['bet_against']
            totl = bet_against+ bet_for
            percent_for = (bet_for / totl) * 100
            percent_against = (100 - percent_for)
            print(percent_for, percent_against)

            total = Betting.objects.filter(forecast=forecast).count()
        except Exception:
            total_wagered = 0
            percent_for = 0
            percent_against = 0
            bet_for = 0
            bet_against = 0
            total = Betting.objects.filter(forecast=forecast).count()
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, bet_for=bet_for,
                         bet_against=bet_against))
    return data


def forecast_result_data(forecast_live):
    data = []
    for f in forecast_live:
        forecast = f.forecast
        date = current.date()
        bet_start = forecast.start.date()
        if date == bet_start:
            start = forecast.start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = forecast.start
            today = 'no'
        betting_for = Betting.objects.filter(forecast=forecast, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=forecast, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=forecast).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=forecast).aggregate(bet_against=Sum('bet_against'))['bet_against']
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
            bet_against = 0
            total = 0
        if f.won == 'bet_for':
            won = "Yes"
            # waggered = bet_for
            try:
                if betting_against > 0:
                    ratio = 1 + round((bet_for / total), 2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        else:
            won = "No"
            # waggered = bet_against
            try:
                if betting_for > 0:
                    ratio = 1 + round((bet_against / total), 2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        print(ratio)
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=won,  # waggered=waggered,
                         ratio=ratio,
                         bet_against=bet_against, bet_for=bet_for))

    return data

@csrf_exempt
def get_sub_cat(request):
    if request.method == "POST":
        cat = Category.objects.get(id=int(request.POST.get('identifier','')))
        sub = SubCategory.objects.filter(category=cat).order_by('name')
        data = [dict(id=x.id, name=x.name) for x in sub]
        return HttpResponse(json.dumps(data))


def forecast_live_view(category):
    data = []
    live = ForeCast.objects.filter(approved=True, category=category, status__name='In-Progress').order_by("-created")
    for f in live:
        date = current.date()

        bet_start = f.expire.date()

        if date == bet_start:
            start = f.expire

            today = 'no'
        else:
            start = f.expire
            start = start.time().strftime("%I:%M:%S")
            today = "yes"
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()
        try:
            total_wagered = betting_against + betting_for
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))['bet_against']
            totl = bet_against+ bet_for
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
    return data


def forecast_result_view(category):
    data = []

    result = ForeCast.objects.filter(approved=True, category=category, status__name='Closed').order_by("-created")
    for f in result:
        date = current.date()
        bet_start = f.start.date()
        if date == bet_start:
            start = f.start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = f.start
            today = 'no'
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

        try:
            bet_for = Betting.objects.filter(forecast=f).aggregate(bet_for=Sum('bet_for'))['bet_for']
            bet_against = Betting.objects.filter(forecast=f).aggregate(bet_against=Sum('bet_against'))['bet_against']
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
            bet_against = 0
            total = 0
        if f.won == 'bet_for':
            won = "YES"
            # waggered = bet_for
            try:
                if betting_against > 0:
                    ratio = 1 + round((bet_for / total), 2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        else:
            won = "NO"
            # waggered = bet_against
            try:
                if betting_for > 0:
                    ratio = 1 + round((bet_against / total), 2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=f,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won=won,  # waggered=waggered,
                         ratio=ratio,
                         bet_against=bet_against, bet_for=bet_for))
        print(data)
    return data


def main_page(request):
    return render(request, 'main_page.html')