"""
WSGI config for fblogin project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.11/howto/deployment/wsgi/
"""

import os
import sys
from django.core.wsgi import get_wsgi_application
sys.path.append("/home/lawrato/venv/lib/python2.7/site-packages/")
sys.path.append("/home/lawrato/venv/lib/python2.7/")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fblogin.settings")

application = get_wsgi_application()
