"""
WSGI config for setting project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Set Django settings module (using single settings.py for all environments)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.settings')

# Django WSGI application
application = get_wsgi_application()

# Vercel compatibility - provide both 'handler' and 'app' variables
handler = application
app = application
