"""
WSGI config for cloud_notepad project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cloud_notepad.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
