from .models import *
from django.db.models import Sum


def allocate_points():

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
            total = (bet_against + bet_for)
            f.user.market_fee += total * 0.05
            f.user.save()
            f.save()
            total -= total * 0.10

        except Exception:
            bet_for = 0
            bet_against = 0
            total = 0
        if bet_for == bet_against:
            if f.won == "yes":
                ratio = 1
                forecast_data(f, ratio, total, "yes")
            else:
                ratio = 1
                forecast_data(f, ratio, total, "no")
        elif bet_for > 0:
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
    return "Points allocated"


def forecast_data(forecast, ratio, total, status):
    betting = Betting.objects.filter(forecast=forecast)

    for b in betting:
        bet_for = b.bet_for
        bet_against = b.bet_against
        # if bet_for > 0 and bet_against == 0:
        #     if status == "yes":
        #         b.users.successful_forecast += 1
        #         b.users.fg_points_won += b.bet_for * ratio
        #         b.users.market_fee_paid += bet_for * 0.10
        #         b.users.save()
        #         b.save()
        #     else:
        #         b.users.unsuccessful_forecast += 1
        #         b.users.fg_points_lost += b.bet_for * ratio
        #         b.users.market_fee_paid += bet_for * 0.10
        #         b.users.save()
        #         b.save()
        # elif bet_against > 0 and bet_for == 0:
        #     if status == "no":
        #         b.users.successful_forecast += 1
        #         b.users.fg_points_won += b.bet_against * ratio
        #         b.users.successful_forecast += 1
        #         b.users.market_fee_paid += bet_for * 0.10
        #         b.users.save()
        #         b.save()
        #     else:
        #         b.users.unsuccessful_forecast += 1
        #         b.users.fg_points_lost += b.bet_against
        #         b.users.market_fee_paid += bet_for * 0.10
        #         b.users.save()
        #         b.save()
        if bet_for == 0 and bet_against == 0:
            b.forecast.won = "NA"
            b.forecast.save()
            b.save()
        elif status == "yes":
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
            elif bet_against == bet_for:
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.successful_forecast += 1
                b.users.save()
                b.save()
            if bet_for == 0 and bet_against > 0:
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
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
            elif bet_against == bet_for:
                b.users.fg_points_won += bet_against * ratio
                b.users.market_fee_paid += bet_against * 0.10
                b.users.fg_points_lost += bet_for
                b.users.successful_forecast += 1
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()
            elif bet_for > 0 and bet_against == 0:
                b.users.fg_points_won += bet_for * ratio
                b.users.market_fee_paid += bet_for * 0.10
                b.users.unsuccessful_forecast += 1
                b.users.save()
                b.save()

if __name__ == "__main__":
    allocate_points()