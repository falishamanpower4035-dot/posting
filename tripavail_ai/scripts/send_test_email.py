#!/usr/bin/env python3
import os
import sys
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config import settings

def main(msg: str = "TripAvail SMTP test") -> int:
    try:
        sender = settings.SMTP_USER
        receiver = settings.NOTIFY_EMAIL
        host = settings.SMTP_HOST
        port = int(settings.SMTP_PORT)
        password = settings.SMTP_PASSWORD
        if not password:
            print("SMTP_PASSWORD is empty")
            return 2
        m = MIMEMultipart()
        m['From'] = sender
        m['To'] = receiver
        m['Subject'] = 'TripAvail SMTP Test'
        m.attach(MIMEText(msg, 'plain'))
        with smtplib.SMTP_SSL(host, port) as s:
            s.login(sender, password)
            s.send_message(m)
        print(f"SENT to {receiver}")
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main("Manual SMTP connectivity test from server"))
