# api/utils/email_sender.py
import aiosmtplib
from email.mime.text import MIMEText
from api.config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL

async def send_email(to_email: str, otp: int):
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}. It will expire in 5 minutes."

    msg = MIMEText(body)
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=SMTP_USER,
        password=SMTP_PASS,
    )
