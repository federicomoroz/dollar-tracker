import os


SENDGRID_API_KEY       = os.getenv("SENDGRID_API_KEY", "")
SENDER_EMAIL           = os.getenv("SENDER_EMAIL", "")
FETCH_INTERVAL_MINUTES = int(os.getenv("FETCH_INTERVAL_MINUTES", "60"))
ALERT_COOLDOWN_HOURS   = int(os.getenv("ALERT_COOLDOWN_HOURS", "4"))
