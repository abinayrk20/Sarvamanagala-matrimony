"""
WSGI config for Sarvamangala Matrimony project.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sarvamangala.settings')
application = get_wsgi_application()
