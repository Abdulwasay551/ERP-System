"""
WSGI config for setting project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Use production settings for Vercel deployment
if os.environ.get('VERCEL'):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.production')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setting.settings')

application = get_wsgi_application()
