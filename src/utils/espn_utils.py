import logging
from datetime import datetime, timedelta

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="temporary_key_for_ingest_script",
        ESPN_CLIENT={}  # Bypasses the config lookups smoothly
    )

