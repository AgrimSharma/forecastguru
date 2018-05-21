from .models import *
import datetime


def update_close_status():
    now = datetime.datetime.now()
    status = Status.objects.get(name='Closed')
    ForeCast.objects.filter(approved=True, expire__lte=now).update(status=status)
    return "updated"


def update_in_progress():
    now = datetime.datetime.now()
    status = Status.objects.get(name='In-Progress')
    ForeCast.objects.filter(approved=True, start__gte=now,expire__lte=now).update(status=status)
    return "updated"


def update_closing_soon():
    now = datetime.datetime.now()
    status = Status.objects.get(name='Closing Soon')
    ForeCast.objects.filter(approved=True, start__lte=now, expire__gte=now).update(status=status)
    return "updated"


update_close_status()
# update_closing_soon()
# update_in_progress()