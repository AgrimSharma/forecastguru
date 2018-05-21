from alpha.models import *
import datetime
from django.db.models import Sum


def allocate():
    current = datetime.datetime.now()
    current = datetime.datetime.strftime(current, "%m/%d/%Y %I:%M %p")
    current = datetime.datetime.strptime(current, "%m/%d/%Y %I:%M %p")
    expired = current - datetime.timedelta(hours=2)
    forecast = ForeCast.objects.filter(expire__gte=expired, expire__lte=current, status__name='Closed')
    for f in forecast:
        betting_for = Betting.objects.filter(forecast=f, bet_for__gt=0).count()
        betting_against = Betting.objects.filter(forecast=f, bet_against__gt=0).count()

        betting_sum = Betting.objects.filter(forecast=forecast).aggregate(
            bet_for=Sum('bet_for'), bet_against=Sum('bet_against'))
        total_wagered = betting_sum['bet_for'] + betting_sum['bet_against']
        bet_for = betting_sum['bet_for']
        bet_against = betting_sum['bet_against']
        # bet_for_ratio = (betting_against + betting_for)/betting_for
        # bet_against_ratio = (betting_against + betting_for)/betting_against
        total = total_wagered - total_wagered * f.market_fee
        if betting_against == 0 or betting_for == 0:
            return " Can't process as Bet For OR Bet Against Can't be 0"
        elif f.won == 'bet_for':
            if betting_for > betting_against:
                total_left = total - bet_for
                forecast_data(forecast, total_left, bet_for)
            elif betting_against > bet_for:
                total_left = total - bet_for
                forecast_data(forecast, total_left, bet_for)
        elif f.won == 'bet_against':
            if betting_for > betting_against:
                total_left = total - bet_for
                forecast_data(forecast, total_left, bet_against)
            elif betting_against > bet_for:
                total_left = total - bet_for
                forecast_data(forecast, total_left, bet_against)


def forecast_data(forecast, total_left, bet):
    bets = Betting.objects.filter(forecast=forecast)
    for b in bets:
        if b.bet_for:
            b.users.fg_points_won = b.user.fg_points_won + (total_left * b.bet_for / bet)
            b.users.fg_points_total = b.users.fg_points_total + b.users.fg_points_won + b.users.fg_points_bought + b.users.fg_points_free
            b.users.successful_forecast = b.users.successful_forecast + 1
            b.save()
        else:
            b.user.fg_points_lost = b.user.fg_points_lost - b.bet_against
            b.users.fg_points_total = b.users.fg_points_total - b.users.fg_points_lost + b.users.fg_points_bought + b.users.fg_points_free
            b.users.unsuccessful_forecast = b.users.unsuccessful_forecast + 1
            b.save()


allocate()