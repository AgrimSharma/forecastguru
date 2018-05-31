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
# from background_task import background


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
            f.user.forecast_participated += 1

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
    # import pdb;pdb.set_trace()
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
        status = "yes" if f.won == "yes" else "no"
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against),
                         forecast=f, total=total, start=start,
                         total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against, bet_for=bet_for))

    return render(request, 'forecast_result.html', {"live": data, 'banner': banner})


def get_ratio(bet_for, bet_against, total, status):
    ratio = 0
    if status == 'yes':
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
        bet_for = Betting.objects.filter(users=profile, forecast__status__name="In-Progress").aggregate(bet_for=Sum('bet_for'))['bet_for']
        bet_against = Betting.objects.filter(users=profile, forecast__status__name="In-Progress").aggregate(bet_against=Sum('bet_against'))['bet_against']
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
        profile.fg_points_total = profile.fg_points_free + profile.fg_points_bought + profile.fg_points_won -\
                                  profile.fg_points_lost + profile.market_fee - profile.market_fee_paid
        profile.save()

    return render(request, 'user_profile.html', {"profile": profile,
                                                 "date_joined":date_joined,
                                                 "success":int(suc_per),
                                                 "unsuccess": int(unsuc_per),
                                                 "user": request.user.username,
                                                 "point": point,
                                                 "total": total,
                                                 "status": predict_status(profile)
                                                 })


def predict_status(profile):
    if 0 <= profile.forecast_participated < 25:
        status = "Beginner"
        return status
    elif 25 <= profile.forecast_participated < 75:
        status = "Intermediate"
        return status
    elif profile.forecast_participated > 75:
        status = "Guru"
        return status


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
        # except Exception:
            # return HttpResponse(json.dumps(dict(message='success')))
    else:
        return HttpResponse(json.dumps(dict(message='Please use POST')))


# @background(schedule=datetime.timedelta(minutes=20))
def allocate_points(request):

    forecast = ForeCast.objects.filter(status__name='Closed', verified=True)
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
            total = (bet_against + bet_for)
            f.user.market_fee += total * 0.05
            f.user.save()
            f.save()
            total -= total * 0.10

        except Exception:
            bet_for = 0
            bet_against = 0
            total = 0

        if bet_for > 0:
            if bet_against == 0 and f.won == 'yes':
                ratio = 1
                forecast_data(f, ratio, total, "yes")
            elif bet_against > 0 and f.won == 'yes':
                ratio = (int(1 + round((bet_against / total), 2)))
                forecast_data(f, ratio, total, "yes")
            elif f.won == 'no' and bet_against == 0:
                ratio = 0
                forecast_data(f, ratio, total, "no")

        elif bet_against > 0:
            if bet_for == 0 and f.won == 'no':
                ratio = 1
                forecast_data(f, ratio, total, "no")
            elif bet_for > 0 and f.won == 'no':
                ratio = (int(1 + round((bet_for / total), 2)))
                forecast_data(f, ratio, total, "no")
            elif f.won == 'yes' and bet_for == 0:
                ratio = 0
                forecast_data(f, ratio, total, "yes")
        elif bet_for == 0 and bet_against == 0:
            f.won = "No Result."
            f.save()
    return HttpResponse('Success')


def forecast_data(forecast, ratio, total, status):
    betting = Betting.objects.filter(forecast=forecast)
    import pdb;pdb.set_trace()
    for b in betting:
        bet_for = b.bet_for
        bet_against = b.bet_against
        if status == "yes":
            if bet_for > 0 and bet_against == 0:
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.successful_forecast += 1
                b.users.save()
                b.save()
            elif bet_for > 0 and bet_against > 0:
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.successful_forecast += 1
                b.users.fg_points_lost += bet_against
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()

        elif status == "no":
            if bet_against > 0 and bet_for == 0:
                b.users.fg_points_won += bet_against * ratio
                b.users.market_fee_paid += bet_against * 0.10
                b.users.successful_forecast += 1
                b.users.save()
                b.save()
            elif bet_for > 0 and bet_against > 0:
                b.users.fg_points_won += bet_against * ratio
                b.users.market_fee_paid += bet_against * 0.10
                b.users.fg_points_lost += bet_for
                b.users.successful_forecast += 1
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()



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
    account.fg_points_total += account.fg_points_bought
    account.save()
    return HttpResponseRedirect("/user_profile/")


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

        forecast_result = Betting.objects.filter(forecast__approved=True, forecast__status__name='Closed', users=account).order_by("forecast__expire")
        forecast_approval = Betting.objects.filter(forecast__approved=False, users=account).order_by("forecast__expire")

        return render(request, 'my_friend.html', {"live": live_forecast_data(forecast_live),
                                                  "result": forecast_result_data(forecast_result),
                                                  "approval": forecast_approval,
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


def not_approved(forecast):
    data = []

    for f in forecast:
        date = current.date()
        forecast = f.forecast
        bet_start = forecast.expire.date()

        if date == bet_start:
            start = forecast.expire
            start = start.time().strftime("%I:%M:%S")
            today = 'yes'
        else:
            start = forecast.expire
            today = "no"
        data.append(dict(percent_for=0, percent_against=0, forecast=f,
                         total=0, start=start, total_user=0,
                         betting_for=0, betting_against=0, today=today,
                         participants=0, bet_for=0,
                         bet_against=0))
        print(data)
    return data


def live_forecast_data(forecast_live):
    data = []

    for f in forecast_live:
        date = current.date()
        forecast = f.forecast
        bet_start = forecast.expire.date()

        if date == bet_start:
            start = forecast.expire
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
        if f.won == 'yes':
            try:
                if betting_against > 0:
                    ratio = 1 + round((bet_against / total), 2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        elif f.won == "No":

            try:
                if betting_for > 0:
                    ratio = 1 + round((bet_for / total), 2)
                else:
                    ratio = 0
            except Exception:
                ratio = 1
        status = 'yes' if forecast.won == "yes" else 'no'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status), bet_against=bet_against, bet_for=bet_for))

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
    forecast_live = ForeCast.objects.filter(approved=True, category=category, status__name='In-Progress').order_by("-created")
    for f in forecast_live:
        date = current.date()
        forecast = f.forecast
        bet_start = forecast.expire.date()

        if date == bet_start:
            start = forecast.expire
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


def forecast_result_view(category):
    data = []

    forecast_live = ForeCast.objects.filter(approved=True, category=category, status__name='Closed').order_by("-created")
    for f in forecast_live:
        forecast = f
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
        status = 'yes' if forecast.won == "yes" else 'no'
        data.append(dict(percent_for=int(percent_for), percent_against=int(percent_against), forecast=forecast,
                         total=total, start=start, total_user=betting_for + betting_against,
                         betting_for=betting_for, betting_against=betting_against, today=today,
                         participants=total_wagered, won="Yes" if f.won == 'yes' else 'No',  # waggered=waggered,
                         ratio=get_ratio(bet_for, bet_against, total, status),
                         bet_against=bet_against, bet_for=bet_for))
        print(data)
    return data


def main_page(request):
    return render(request, 'main_page.html')