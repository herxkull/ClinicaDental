import os
import sys
import django

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.conf import settings

print(f"GOOGLE_CLIENT_ID: {repr(settings.GOOGLE_CLIENT_ID)}")
print(f"GOOGLE_CLIENT_SECRET: {repr(settings.GOOGLE_CLIENT_SECRET)}")
