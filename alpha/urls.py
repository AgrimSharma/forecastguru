"""fblogin URL Configuration

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
from django.conf.urls import url
from .views import *

urlpatterns = [
    url(r'^accounts/profile/', test, name='home_page'),
    url(r'^create_forecast/', create_forecast, name='create_forecast'),
    url(r'^trending/', trending_forecast, name='trending'),
    url(r'^result_declared/', forecast_result, name='forecast_result'),
    url(r'^my_result/', result_not_declared, name='result_not_declared'),
    url(r'^closing_soon/', closing_soon, name='closing_soon'),
    url(r'^invite_friends/', invite_friends, name='invite_friends'),
    url(r'^device_data_android/', device_data_android, name='device_data_android'),
    url(r'^live_forecast/', live_forecast, name='live_forecast'),
    url(r'^result_save/', result_save, name='result_save'),
    url(r'^user_profile/', profile, name='user_profile'),
    url(r'^forecast/(?P<userid>\d+)/$', betting, name='betting'),
    url(r'^bet_save/', bet_post, name='bet_save'),
    url(r'^allocate_points/', allocate_points, name='allocate_points'),
    url(r'^search_result/', search_result, name='search_result'),
    url(r'^payu/', home, name='payu'),
    url(r'^payment/', payment, name='payment'),
    url(r'^payubiz-success/$', payu_success, name='payu_success'),
    url(r'^session/', session, name='session'),

    url(r'^payubiz-failure/$', payu_failure, name='payu_failure'),

    url(r'^payubiz-cancel/$', payu_cancel, name='payu_cancel'),
    url(r'^category/', category, name='category'),
    url(r'^facebook/', facebook_category, name='facebook_category'),
    url(r'^thank_you/', thank_you, name='thank_you'),

    url(r'^category_search/(?P<userid>\d+)/$', category_search, name='category_search'),
    url(r'^sub_category_data/(?P<userid>\d+)/$', sub_category_data, name='sub_category_data'),
    url(r'^my_forecast/', my_forecast, name='my_forecast'),
    url(r'^private/', my_forecast_private, name='private'),
    url(r'^logout_user/', logout_view, name='logout_user'),
    url(r'^home/', blank_page, name='blank_page'),
    url(r'^login_page/', login_page, name='login_page'),
    url(r'^signup_page/', signup_page, name='signup_page'),
    url(r'^get_forecast/', get_forecast, name='get_forecast'),
    url(r'^get_sub_cat/', get_sub_cat, name='get_sub_cat'),
    url(r'^get_sub_source/', get_sub_source, name='get_sub_source'),
    url(r'^shoping/$', payments, name="payments"),
    url(r'^success$', payment_success, name="payment_success"),
    url(r'^failure$', payment_failure, name="payment_failure"),
    url(r'^closed_status/', update_close_status, name="closed_status"),
    url(r'^terms_and_conditions/', terms, name="terms"),
    url(r'^faqs/', faq, name="faq"),
    url(r'^privacy_policy/', privacy, name="privacy_policy"),
    url(r'^import_csv/', import_csv, name="import_csv"),
    url(r'^', main_page, name='main_page'),

]

handler404 = e_handler404
handler500 = e_handler500