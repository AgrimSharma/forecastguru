# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.viewsets import generics
from .serailizers import *
from rest_framework import viewsets
from django.db.models import Sum
import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout


def id_generator(fname, lname):
    r = re.compile(r"\s+", re.MULTILINE)
    return r.sub("", str(fname)).capitalize() + str(lname).capitalize() + str(random.randrange(1111, 9999))


class LoginSignUpGeneric(generics.CreateAPIView):
    queryset = Authentication.objects.all()
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        if request.data:
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            userID = request.data['facebook_id']
            email = request.data['email']
        else:
            first_name = request.POST.get('first_name',"")
            last_name = request.POST.get('last_name',"")
            userID = request.POST.get('facebook_id', "")
            email = request.POST.get('email',"")
        try:
            user = User.objects.get(username=userID)
            auth = authenticate(request, username=userID, password=userID)

            if auth:
                login(request, auth)
                return JsonResponse(dict(status=200, message='Login Success', url="https://fstage.sirez.com/referral_code/"))
            else:
                return JsonResponse(dict(status=400, message='Login Fail', url=""))
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
                return JsonResponse(dict(status=200, message="SignUP Success", url="https://fstage.sirez.com/referral_code/" ))
            else:
                return JsonResponse(
                    dict(status=400, message="SignUP Fail", url=""))


class SignUpGeneric(generics.CreateAPIView):
    queryset = Authentication.objects.all()
    serializer_class = SignUpSerializer

    def create(self, request, *args, **kwargs):
        try:
            email = request.data['email']
            auth = Authentication.objects.get(email=email)
            return JsonResponse(dict(status=200, message="Already Registered", data=dict(
                id=auth.id,
                first_name=auth.first_name,
                last_name=auth.last_name,
                facebook_id=auth.facebook_id,
                email=auth.email,
                mobile=auth.mobile,
                gender=auth.gender
            )))
        except Exception:
            serializer = SignUpSerializer(data=request.data)
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            facebook_id = request.data['facebook_id']
            email = request.data['email']
            if serializer.is_valid():
                serializer.save()
                user = User.objects.create(username=facebook_id, first_name=first_name, last_name=last_name, email=email)
                user.set_password(facebook_id)
                auth = Authentication.objects.get(id=serializer.data['id'])
                joining = JoiningPoints.objects.get(id=1).points
                auth.joining_points = joining
                auth.referral_code = id_generator(auth.first_name, auth.last_name)
                auth.save()
                return JsonResponse(dict(status=200, message="saved successful", data=serializer.data))
            else:
                return JsonResponse(dict(status=400, message="some thing is missing"))


class LastLoginApi(generics.CreateAPIView):
    """
      This API is designed to work with PostMan.\n
      API contains below fields \n
      **login_date(yyyy-mm-dd) and user_id**
    """
    queryset = Authentication.objects.all().order_by('created')
    serializer_class = LastLoginSerializer

    def create(self, request, *args, **kwargs):
        login_date = request.data['login_date']
        user_id = request.data['user_id']

        try:
            auth = Authentication.objects.get(id=int(user_id))
            login_last = datetime.datetime.strptime(login_date, "%Y-%m-%d").date()
            difference = login_last - auth.last_login
            try:
                referred = ReferralCodeRegistered.objects.filter(user_joined=auth).count()
            except Exception:
                referred = 0
            if difference.days == 1 and auth.login_count < 7 and auth.last_login < login_last:
                auth.login_count += 1
                points = DailyFreePoints.objects.get(days=auth.login_count)
                auth.points_earned += points.points
                auth.last_login = datetime.datetime.strptime(login_date, "%Y-%m-%d")
                auth.save()

                return Response(data=dict(status=200, message="Points Credited", reffered=True if referred > 0 else False))
            else:
                auth.last_login = datetime.datetime.strptime(login_date, "%Y-%m-%d")
                auth.login_count = 0
                auth.save()
                return Response(data=dict(status=200, message="No points credited ", reffered=True if referred > 0 else False))
        except Exception:
            return JsonResponse(dict(status=400, message="User Not Found"))


class ForecastGeneric(viewsets.ModelViewSet):
    queryset = ForeCast.objects.all().order_by('expire')
    serializer_class = ForecastSerializers

    def create(self, request, *args, **kwargs):
        serializer = ForecastSerializers(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return JsonResponse(dict(status=200, message="Forecast Created", data=serializer.data))
        else:
            return JsonResponse(dict(status=400, message="Some error"))


class GetForeCastGeneric(generics.CreateAPIView):
    queryset = ForeCast.objects.all().order_by('expire')
    serializer_class = GetForecastSerializers

    def create(self, request, *args, **kwargs):
        private = []
        public = []
        user_id = request.data['user_id']
        forecast = ForeCast.objects.filter(user__id=int(user_id))
        for f in forecast:
            if f.private.id == 1:
                private.append(dict(category=f.category.id,
                                    sub_category=f.sub_category.id,
                                    heading=f.heading,
                                    tags=f.tags,
                                    status=f.status.id,
                                    private=f.private.id,
                                    expire=f.expire,
                                    id=f.id
                                    ))
            else:
                public.append(dict(category=f.category.id,
                                   sub_category=f.sub_category.id,
                                   heading=f.heading,
                                   tags=f.tags,
                                   status=f.status.id,
                                   private=f.private.id,
                                   expire=f.expire,
                                   id=f.id
                                   ))
        return JsonResponse(dict(status=200, private_forecast=private, public_forecast=public))


class PlaceBetGeneric(generics.ListCreateAPIView):
    queryset = Betting.objects.all()
    serializer_class = PlaceBetSerializers

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        forecast_id = request.data['forecast_id']
        points = int(request.data['points'])
        bet_id = int(request.data['bet_id'])
        if not user_id or not forecast_id or not points or not bet_id:
            return JsonResponse(dict(status=400, message='All fields are mandatory'))
        else:
            try:
                user = Authentication.objects.get(id=int(user_id))
            except Exception:
                return JsonResponse(dict(status=400, message='User does not exists'))
            try:
                forecast = ForeCast.objects.get(id=int(forecast_id))
            except Exception:
                return JsonResponse(dict(status=400, message='Forecast does not exists'))
            try:
                bet = Betting.objects.get(users=user, forecast=forecast)
                if bet_id == 1:
                    bet.bet_for += points
                elif bet_id == 2:
                    bet.bet_against += points
                else:
                    return JsonResponse(dict(status=400, message='BET id can be 1 or 2'))
                user.forecast_played += 1
                user.save()
                bet.save()
                return JsonResponse(dict(status=200, message='Bet Updated Successful'))

            except Exception:
                if bet_id == 1:
                    bet = Betting.objects.create(users=user, forecast=forecast,
                                                 bet_for=points)
                elif bet_id == 2:
                    bet = Betting.objects.create(users=user, forecast=forecast,
                                                 betagainst=points)
                else:
                    return JsonResponse(dict(status=400, message='BET id can be 1 or 2'))
                bet.save()
                user.forecast_played += 1
                user.save()
                return JsonResponse(dict(status=200, message='Bet Saved Successful'))


class GetPlayedForecastGeneric(generics.CreateAPIView):
    queryset = Betting.objects.all()
    serializer_class = GetPlayedForecastSerializers

    def create(self, request, *args, **kwargs):
        data = []
        user_id = request.data['user_id']
        forecast = Betting.objects.filter(users__id=int(user_id))
        for f in forecast:
            data.append(dict(forecast=dict(
                heading=f.forecast.heading, id=f.forecast.id,category=f.forecast. category.id,
                sub_category=f.forecast.sub_category.id, tags=f.forecast.tags,
                private=f.forecast.private.id, status=f.forecast.status.id),
                user=f.users.id, bet_for=f.bet_for,
                bet_against=f.bet_against, id=f.id
            ))
        return JsonResponse(dict(status=200, data=data))


class ReferralCodeGeneric(generics.CreateAPIView):
    queryset = ReferralCodeRegistered.objects.all()
    serializer_class = ReferralCodeSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_joined']
        referral_code = request.data['referral_code']

        try:
            user = Authentication.objects.get(referral_code=referral_code)
            referred = Authentication.objects.get(id=user_id)
            try:
                ReferralCodeRegistered.objects.get(referral_code=referral_code, user_joined=referred)
                return JsonResponse(dict(status=200, message="Already Used"))
            except Exception:
                ReferralCodeRegistered.objects.create(referral_code=referral_code, user_joined=referred)
                if referred.id != user.id:
                    points = ReferralCodePoints.objects.get(id=1)
                    user.points_earned += int(points.points)
                    user.save()
                    referred.points_earned += int(points.points)
                    referred.save()
                    return JsonResponse(dict(status=200, message="Thanks for entering code"))
                else:
                    return JsonResponse(dict(status=200, message="Wrong Referral"))
        except Exception:
            return JsonResponse(dict(status=400, message="Wrong Referral Code"))


class InterestAPI(generics.ListCreateAPIView):
    queryset = UserInterest.objects.all()
    serializer_class = UserInterestSerializer

    def list(self, request, *args, **kwargs):
        sub_category = SubCategory.objects.all()
        return Response(dict(status=200, interest=[dict(id=s.id, name=s.name, image=s.image) for s in sub_category]))

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        interest_list = request.data['interest']
        try:
            user = Authentication.objects.get(id=user_id)
        except Exception:
            return Response(dict(status=400, interest="User Doesn't exists"))
        try:
            interest = UserInterest.objects.get(user=user)
        except Exception:
            interest = UserInterest.objects.create(user=user)
        for i in interest_list.split(','):
            sub = SubCategory.objects.get(id=int(i))
            interest.interest.add(sub)
            interest.save()
        return Response(dict(status=200, interest="Interest Saved"))


class ResultGeneric(generics.ListCreateAPIView):
    queryset = ForeCast.objects.all()
    serializer_class = ResultSerializer

    def list(self, request, *args, **kwargs):
        data = []
        forecast = ForeCast.objects.filter(status__name='Result Declared').order_by('expire')
        for f in forecast:
            data.append(dict(category=f.category.id,
                             sub_category=f.sub_category.id,
                             heading=f.heading,
                             tags=f.tags,
                             status=f.status.id,
                             private=f.private.id,
                             expire=f.expire,
                             id=f.id
                             ))
        return Response(dict(data=data, status=200))

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        try:
            auth = Authentication.objects.get(id=user_id)
        except Exception:
            return Response(dict(status=400, message='User Error'))
        data = []
        forecast = Betting.objects.filter(forecast__status__name='Result Declared', users=auth).order_by('forecast__expire')
        for f in forecast:
            data.append(dict(category=f.forecast.category.id,
                             sub_category=f.forecast.sub_category.id,
                             heading=f.forecast.heading,
                             tags=f.forecast.tags,
                             status=f.forecast.status.id,
                             private=f.forecast.private.id,
                             expire=f.forecast.expire,
                             id=f.forecast.id,
                             bet_for=f.bet_for,
                             bet_against=f.bet_against,
                             ))
        return Response(dict(data=data, status=200))


class UserProfileGeneric(generics.CreateAPIView):
    queryset = Authentication.objects.all()
    serializer_class = AuthenticationSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        try:
            profile = Authentication.objects.get(id=user_id)
        except Exception:
            return Response(dict(status=400, message='User Error'))
        created = datetime.datetime.strftime(profile.created, '%b %d, %Y')
        try:
            bet_for = \
                Betting.objects.filter(users=profile, forecast__status__name="In-Progress").aggregate(
                    bet_for=Sum('bet_for'))['bet_for']
        except Exception:
            bet_for = 0
        try:
            bet_for_close = \
                Betting.objects.filter(users=profile, forecast__status__name="Closed").aggregate(
                    bet_for=Sum('bet_for'))['bet_for']
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

        if not bet_against:
            bet_against = 0
        if not bet_for:
            bet_for = 0
        if not bet_for_close:
            bet_for_close = 0
        if not bet_against_close:
            bet_against_close = 0

        point = bet_against + bet_for + bet_for_close + bet_against_close

        total = profile.joining_points + profile.points_earned + profile.market_fee + profile.points_won - profile.points_lost - profile.market_fee_paid - point
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
        profile.market_fee_paid = int(profile.points_won * 0.10)
        profile.save()

        fore = ForeCast.objects.filter(user=profile).count()
        return Response({"date_joined": created,
                         "success": int(suc_per),
                         "unsuccess": int(unsuc_per),
                         "user": request.user.username,
                         "point": point,
                         "total_forecast": fore,
                         "status": predict_status(profile, suc_per),
                         "balance": total,
                         "points_earned": profile.points_earned,
                         "points_won": profile.points_won,
                         "points_lost": profile.points_lost,
                         })


def predict_status(profile, suc_per):
    if profile.forecast_participated < 10 and suc_per < 50:
        status = "Beginner"
        return status
    elif profile.forecast_participated >= 10 and suc_per >= 50:
        status = "Expert"
        return status
    elif profile.forecast_participated >= 30 and suc_per >= 70:
        status = "Influencer"
        return status
    elif profile.forecast_participated >= 50 and suc_per >= 90:
        status = "Guru"
        return status
    else:
        status = "Beginner"
        return status


class AdvertisementPointsGeneric(generics.CreateAPIView):
    queryset = AdvertisementPoints.objects.all()
    serializer_class = AdvertisementPointsSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        try:
            user = Authentication.objects.get(id=user_id)
        except Exception:
            return Response(dict(status=400, message="User Not found"))
        points = AdvertisementPoints.objects.latest('id').points
        user.points_earned += points
        return Response(dict(status=200, message="{} points credited".format(points)))


class RatingGeneric(generics.ListCreateAPIView):
    queryset = RateApp.objects.all()
    serializer_class = RateAppSerializer

    def create(self, request, *args, **kwargs):
        rating = request.data['rating']
        serializer = RateAppSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            if float(rating) >= 4:
                data = serializer.data
                data['redirect_url'] = "https://play.google.com/store/apps/details?id=com.sirez.forecastguru"
                return JsonResponse(dict(status=200, message="saved successful", data=data))
            else:
                return JsonResponse(dict(status=200, message="saved successful", data=serializer.data))
        else:
            return JsonResponse(dict(status=400, message="All fields are mandatory"))


class GetRatingGeneric(generics.CreateAPIView):
    queryset = RateApp.objects.all()
    serializer_class = GetRateAppSerializer

    def create(self, request, *args, **kwargs):
        user_id = request.data['user_id']
        try:
            user = Authentication.objects.get(id=user_id)
        except Exception:
            return Response(dict(status=400, message="User Not found"))
        rating = RateApp.objects.get(user=user)
        return JsonResponse(dict(status=200, message="success", data=dict(
            user=rating.user.email,
            rating=rating.rating,
            feedback=rating.feedback
        )))