import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

def send_email_notification(to_email: str, subject: str, body_html: str, body_text: str = "") -> bool:
    """
    Sends email notifications. Falls back to printing/logging in Mock Mode.
    """
    if settings.is_mock_mode or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        print("\n=== [MOCK EMAIL SENT] ===")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(f"Body:\n{body_text or body_html}")
        print("==========================\n")
        return True
        
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = settings.SMTP_USER
        msg['To'] = to_email
        
        # Attach text & HTML parts
        part1 = MIMEText(body_text or "YuniQ Employee Portal notification.", 'plain')
        part2 = MIMEText(body_html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Connect & send
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_email, msg.as_string())
            
        print(f"Real email notification sent to {to_email} successfully.")
        return True
    except Exception as e:
        print(f"Error sending real email: {e}. Logging notification instead.")
        return False
