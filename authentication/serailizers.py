from rest_framework import serializers
from .models import *
import string, random
import re
from django.utils.translation import ugettext_lazy as _


def id_generator(name):
    r = re.compile(r"\s+", re.MULTILINE)
    return r.sub("", str(name)).capitalize() + str(random.randrange(1111, 9999))


class SignUpSerializer(serializers.ModelSerializer):
    facebook_id = serializers.CharField(help_text=_("User Facebook ID(Character)"))
    first_name = serializers.CharField(help_text=_("User First Name(Character)"))
    last_name = serializers.CharField(help_text=_("User Last Name(Character)"))
    email = serializers.CharField(help_text=_("User Email"))

    class Meta:
        model = Authentication
        fields = ["id", "facebook_id", "first_name", "last_name", "email"]

    def create(self, validated_data):
        auth = Authentication.objects.create(**validated_data)
        return auth


class LastLoginSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User Id field "))
    login_date = serializers.DateField(help_text=_("Today Date YYYY-MM-DD"))

    class Meta:
        model = Authentication
        fields = ["user_id", "login_date"]


class ForecastSerializers(serializers.ModelSerializer):
    category = serializers.IntegerField(help_text=_("Category ID(Integer)"))
    sub_category = serializers.IntegerField(help_text=_("Sub-Category ID(Integer)"))
    user = serializers.IntegerField(help_text=_("User ID(Integer)"))
    heading = serializers.CharField(help_text=_("Forecast Heading(Character)"))
    tags = serializers.CharField(help_text=_("Forecast Search Tags(Character)"))
    expire = serializers.DateTimeField(help_text=_("Date in YYYY-MM-DD HH:MM:SS"))

    class Meta:
        model = ForeCast
        fields = ["id", "category", "sub_category", 'user', "heading","tags","expire"]

    def create(self, validated_data):
        return ForeCast.objects.create(**validated_data)


class GetForecastSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User ID"))

    class Meta:
        model = ForeCast
        fields = ["user_id"]


class PlaceBetSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User ID"))
    forecast_id = serializers.IntegerField(help_text=_("Forecast ID"))
    points = serializers.IntegerField(help_text=_("Points to play"))
    bet_id = serializers.IntegerField(help_text=_("Bet ID 1 for Yes and 2 for No"))

    class Meta:
        model = ForeCast
        fields = ["user_id", "forecast_id", "points", "bet_id"]


class GetPlayedForecastSerializers(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User ID"))

    class Meta:
        model = Betting
        fields = ["user_id"]


class ReferralCodeSerializer(serializers.ModelSerializer):
    referral_code = serializers.CharField(help_text=_("Referral Code"))
    user_joined = serializers.IntegerField(help_text=_("User ID"))

    class Meta:
        model = Betting
        fields = ["referral_code", "user_joined"]


class UserInterestSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True, help_text=_("User ID"))
    interest = serializers.CharField(required=True, help_text=_("Comma separated ID"))

    class Meta:
        model = UserInterest
        fields = ["user_id", "interest"]


class ResultSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User ID"))

    class Meta:
        model = ForeCast
        fields = ["user_id"]


class AuthenticationSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User ID"))

    class Meta:
        model = Authentication
        fields = ["user_id"]


class AdvertisementPointsSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(help_text=_("User ID"))

    class Meta:
        model = AdvertisementPoints
        fields = ["user_id"]


class RateAppSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True,help_text=_("User ID"))
    rating = serializers.CharField(max_length=10, required=True, help_text=_("Rating for APP 1 to 5"))
    feedback = serializers.CharField(max_length=1000, required=True, help_text=_("Feedback for app"))

    class Meta:
        model = RateApp
        fields = ["user_id", "rating", "feedback"]

    def create(self, validated_data):
        auth = RateApp.objects.create(**validated_data)
        return auth


class GetRateAppSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(required=True, help_text=_("User ID"))

    class Meta:
        model = RateApp
        fields = ["user_id"]
