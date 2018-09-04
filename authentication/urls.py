"""forecastguru_api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from .views import *
from rest_framework import routers
from rest_framework.documentation import include_docs_urls

router = routers.DefaultRouter()
router.register(r'forecast', ForecastGeneric)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include_docs_urls(title='ForeCast API', public=False)),
    url(r'^last_login/', LastLoginApi.as_view()),
    url(r'^rate_app/', RatingGeneric.as_view()),
    url(r'^get_user_rating/', GetRatingGeneric.as_view()),
    url(r'^get_forecast/', GetForeCastGeneric.as_view()),
    url(r'^register/', SignUpGeneric.as_view()),
    url(r'^play_forecast/', PlaceBetGeneric.as_view()),
    url(r'^get_play_forecast/', GetPlayedForecastGeneric.as_view()),
    url(r'^referral_code/', ReferralCodeGeneric.as_view()),
    url(r'^user_interest/', InterestAPI.as_view()),
    url(r'^result/', ResultGeneric.as_view()),
    url(r'^login_facebook/', LoginSignUpGeneric.as_view()),
    url(r'^user_profile/', UserProfileGeneric.as_view()),
    url(r'^advertisement_points/', AdvertisementPointsGeneric.as_view()),

]
