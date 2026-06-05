import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional
import datetime

# Log files are written to backend/logs/ (one level up from admin/)
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
INVITATION_LOG_FILE = os.path.join(LOG_DIR, "onboarding_invitations.log")
NOTIFICATION_LOG_FILE = os.path.join(LOG_DIR, "notifications.log")


def _attach_logo_if_exists(msg: MIMEMultipart) -> None:
    """Helper function to load the local yuniq logo and embed it as an inline CID attachment."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    logo_path = os.path.join(base_dir, "frontend", "yuniq logo.png")

    if os.path.exists(logo_path):
        try:
            with open(logo_path, "rb") as f:
                img_data = f.read()
            msg_image = MIMEImage(img_data)
            msg_image.add_header("Content-ID", "<yuniq_logo>")
            msg_image.add_header("Content-Disposition", "inline", filename="yuniq_logo.png")
            msg.attach(msg_image)
        except Exception as e:
            print(f"Failed to attach logo to email: {e}")


def send_onboarding_email(
    to_email: str,
    employee_name: str,
    invitation_token: str,
    role: str,
    sender_name: Optional[str] = None
) -> bool:
    """
    Sends an onboarding invitation email to a newly created employee.
    Falls back to logging the invite to backend/logs/onboarding_invitations.log.
    """
    role_lower = role.lower() if role else ""
    is_manager_role = (
        role in ["Director", "Manager", "CEO", "Senior Manager", "HR Manager", "Management", "IT-admin"] or
        "ceo" in role_lower or
        "hr" in role_lower or
        "manager" in role_lower or
        "director" in role_lower or
        "admin" in role_lower or
        "management" in role_lower or
        "it" in role_lower or
        "system" in role_lower or
        "network" in role_lower or
        "asset" in role_lower or
        "lead" in role_lower or
        "head" in role_lower or
        "vp" in role_lower
    )
    frontend_url = os.environ.get('FRONTEND_URL')
    if not frontend_url or not frontend_url.strip():
        frontend_url = 'http://localhost:3000'

    onboarding_url = f"{frontend_url}/onboarding?token={invitation_token}"

    sender_suffix = f" from {sender_name}" if sender_name else ""
    if is_manager_role:
        subject = f"Welcome to the YuniQ Admin Team! Complete Your Console Setup{sender_suffix}"
        welcome_text = f"Welcome to the YuniQ Management Team! You have been successfully registered with the role of <strong style=\"color: #22c55e;\">{role}</strong>."
        intro_text = "As a manager/administrative staff, you have access to the administrative dashboard to oversee dynamic portal configurations, teams, and operations. Please set up your password and complete your onboarding invitation below:"
    else:
        subject = f"Welcome to YuniQ! Complete Your Onboarding Setup{sender_suffix}"
        welcome_text = f"We are thrilled to welcome you to the YuniQ family! You have been successfully set up as a <strong style=\"color: #22c55e;\">{role}</strong>."
        intro_text = "To log in, view your profile, log timesheets, request leaves, and view your monthly payslips, please set up your password and complete your onboarding:"

    body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Welcome to YuniQ</title></head>
<body style="margin: 0; padding: 0; background-color: #020617; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #020617; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 550px; background-color: #0f172a; border: 1px solid #334155; border-radius: 12px; overflow: hidden;">
          <tr>
            <td style="background: linear-gradient(135deg, #22c55e 0%, #10b981 100%); padding: 35px 40px; text-align: center;">
              <div style="margin-bottom: 10px;"><img src="cid:yuniq_logo" alt="YuniQ Logo" style="height: 45px; max-width: 180px; display: block; margin: 0 auto;"/></div>
              <div style="font-size: 13px; font-weight: 700; color: #020617; text-transform: uppercase; letter-spacing: 3px; margin-top: 5px;">{"Administrative Console" if is_manager_role else "Employee Portal"}</div>
            </td>
          </tr>
          <tr>
            <td style="padding: 40px; line-height: 1.6;">
              <h2 style="font-size: 22px; font-weight: 700; color: #ffffff; margin-top: 0; margin-bottom: 20px;">Hello {employee_name},</h2>
              <p style="color: #94a3b8; font-size: 15px; margin-bottom: 20px;">{welcome_text}</p>
              <p style="color: #94a3b8; font-size: 15px; margin-bottom: 30px;">{intro_text}</p>
              <table border="0" cellpadding="0" cellspacing="0" width="100%" style="margin-bottom: 30px;">
                <tr>
                  <td align="center">
                    <a href="{onboarding_url}" style="background-color: #22c55e; color: #020617; padding: 14px 28px; text-decoration: none; border-radius: 6px; font-weight: 700; font-size: 15px; display: inline-block;">
                      {"Set Up Your Password"}
                    </a>
                  </td>
                </tr>
              </table>
              <div style="border-top: 1px solid #334155; padding-top: 25px;">
                <p style="color: #64748b; font-size: 13px; margin: 0 0 10px 0;">If the button above does not work, copy and paste this URL into your browser:</p>
                <p style="word-break: break-all; font-size: 13px; color: #3b82f6; font-family: monospace; margin: 0; background-color: #1e293b; padding: 12px; border-radius: 6px; border: 1px solid #334155;">{onboarding_url}</p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="background-color: #1e293b; padding: 25px 40px; text-align: center; border-top: 1px solid #334155;">
              <p style="color: #64748b; font-size: 12px; margin: 0;">This is an automated security email. Please do not reply directly to this message.</p>
              <p style="color: #94a3b8; font-size: 12px; font-weight: 600; margin: 10px 0 0 0;">&copy; YuniQ HR Management Team</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.com")
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        smtp_port = 587
    smtp_user = os.getenv("SMTP_USER", "donotreply@tekclansolutions.com")
    smtp_pass = os.getenv("SMTP_PASSWORD", "2mfEedq0VHB58ZWN")
    smtp_from = os.getenv("SMTP_FROM", "donotreply@tekclansolutions.com")

    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("related")
            msg["From"] = smtp_from
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))
            _attach_logo_if_exists(msg)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, to_email, msg.as_string())
            print(f"SMTP Email successfully sent via Zoho to {to_email}!")
            return True
        except Exception as e:
            print(f"SMTP failed to send mail to {to_email}, falling back to logging: {e}")

    # Fallback Logging
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_entry = (
            f"=== ONBOARDING INVITATION SENT ===\n"
            f"Timestamp: {datetime.datetime.utcnow().isoformat()}\n"
            f"Recipient: {employee_name} ({to_email})\n"
            f"Role: {role}\n"
            f"Token: {invitation_token}\n"
            f"Onboarding URL: {onboarding_url}\n"
            f"==================================\n\n"
        )
        with open(INVITATION_LOG_FILE, "a") as f:
            f.write(log_entry)
        print(f"Onboarding logged locally to backend/logs/onboarding_invitations.log for {employee_name}!")
        return True
    except Exception as e:
        print(f"Failed to log invitation locally: {e}")
        return False


def send_notification_email(
    to_email: str,
    employee_name: str,
    subject: str,
    category: str,
    content_html: str,
    status_color: str = None
) -> bool:
    theme_color = status_color if status_color else "#3b82f6"

    body = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>{subject}</title></head>
<body style="margin: 0; padding: 0; background-color: #020617; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #f8fafc;">
  <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color: #020617; padding: 40px 20px;">
    <tr>
      <td align="center">
        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 550px; background-color: #0f172a; border: 1px solid #334155; border-radius: 12px; overflow: hidden;">
          <tr>
            <td style="background: #0f172a; padding: 30px 40px; text-align: center; border-bottom: 2px solid {theme_color};">
              <div style="margin-bottom: 10px;"><img src="cid:yuniq_logo" alt="YuniQ Logo" style="height: 45px; max-width: 180px; display: block; margin: 0 auto;"/></div>
              <div style="font-size: 11px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 3px; margin-top: 5px;">{category}</div>
            </td>
          </tr>
          <tr>
            <td style="padding: 40px; line-height: 1.6;">
              <h2 style="font-size: 20px; font-weight: 700; color: #ffffff; margin-top: 0; margin-bottom: 20px;">Hello {employee_name},</h2>
              <div style="color: #94a3b8; font-size: 15px; margin-bottom: 30px;">{content_html}</div>
            </td>
          </tr>
          <tr>
            <td style="background-color: #1e293b; padding: 25px 40px; text-align: center; border-top: 1px solid #334155;">
              <p style="color: #64748b; font-size: 12px; margin: 0;">This is an automated system email. Please do not reply directly to this message.</p>
              <p style="color: #94a3b8; font-size: 12px; font-weight: 600; margin: 10px 0 0 0;">&copy; YuniQ Operations Team</p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    smtp_host = os.getenv("SMTP_HOST", "smtp.zoho.com")
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
    except ValueError:
        smtp_port = 587
    smtp_user = os.getenv("SMTP_USER", "donotreply@tekclansolutions.com")
    smtp_pass = os.getenv("SMTP_PASSWORD", "2mfEedq0VHB58ZWN")
    smtp_from = os.getenv("SMTP_FROM", "donotreply@tekclansolutions.com")

    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("related")
            msg["From"] = smtp_from
            msg["To"] = to_email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))
            _attach_logo_if_exists(msg)

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_from, to_email, msg.as_string())
            print(f"SMTP Email successfully sent via Zoho to {to_email}!")
            return True
        except Exception as e:
            print(f"SMTP failed to send mail to {to_email}, falling back to logging: {e}")

    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        log_entry = (
            f"=== NOTIFICATION EMAIL SENT ===\n"
            f"Timestamp: {datetime.datetime.utcnow().isoformat()}\n"
            f"Recipient: {employee_name} ({to_email})\n"
            f"Category: {category}\n"
            f"Subject: {subject}\n"
            f"==================================\n\n"
        )
        with open(NOTIFICATION_LOG_FILE, "a") as f:
            f.write(log_entry)
        print(f"Notification logged locally to backend/logs/notifications.log for {employee_name}!")
        return True
    except Exception as e:
        print(f"Failed to log notification locally: {e}")
        return False


def send_leave_status_email(to_email, employee_name, leave_type, from_date, to_date, num_days, reason, status, sender_name=None):
    status_lower = status.lower()
    color = "#22c55e" if "approve" in status_lower else "#ef4444"
    status_text = "APPROVED" if "approve" in status_lower else "REJECTED"
    desc = "Your leave request has been approved by the Admin team." if "approve" in status_lower else "Your leave request has been rejected."
    content_html = f"""
    <p style="color:#ffffff; font-size:16px;">Your leave application status has been updated:</p>
    <div style="background-color:#1e293b; border-left:4px solid {color}; padding:20px; border-radius:6px; margin-bottom:25px;">
      <table border="0" cellpadding="4" style="color:#94a3b8; font-size:14px; width:100%;">
        <tr><td style="font-weight:700;color:#ffffff;width:35%;">Leave Type:</td><td>{leave_type}</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Duration:</td><td>{from_date} to {to_date} ({num_days} day(s))</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Reason:</td><td>{reason or 'Not Specified'}</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Status:</td><td><strong style="color:{color};">{status_text}</strong></td></tr>
      </table>
    </div>
    <p style="color:#64748b;font-size:14px;">{desc}</p>
    """
    sender_suffix = f" by {sender_name}" if sender_name else ""
    return send_notification_email(to_email, employee_name, f"Leave Request {status_text}{sender_suffix} - {leave_type}", "Leave Notification", content_html, color)


def send_performance_review_email(to_email, employee_name, year, quality_rating, collaboration_rating, leadership_rating, comments, sender_name=None):
    color = "#3b82f6"
    avg_rating = round((quality_rating + collaboration_rating + leadership_rating) / 3.0, 2)
    content_html = f"""
    <p style="color:#ffffff;font-size:16px;">A new performance evaluation has been logged for you for the year <strong>{year}</strong>:</p>
    <div style="background-color:#1e293b; border-left:4px solid {color}; padding:20px; border-radius:6px; margin-bottom:25px;">
      <table border="0" cellpadding="4" style="color:#94a3b8;font-size:14px;width:100%;">
        <tr><td style="font-weight:700;color:#ffffff;width:50%;">Quality of Work:</td><td>{quality_rating} / 5.0</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Team Collaboration:</td><td>{collaboration_rating} / 5.0</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Leadership &amp; Initiative:</td><td>{leadership_rating} / 5.0</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;padding-top:10px;">Overall Average:</td><td style="color:{color};font-weight:700;font-size:16px;padding-top:10px;">{avg_rating} / 5.0</td></tr>
      </table>
    </div>
    <p style="color:#64748b;font-size:14px;">Manager Comments: {comments or 'No comments logged.'}</p>
    """
    sender_suffix = f" by {sender_name}" if sender_name else ""
    return send_notification_email(to_email, employee_name, f"Performance Review Logged{sender_suffix} - {year}", "Performance Evaluation", content_html, color)


def send_travel_status_email(to_email, employee_name, destination, departure_date, return_date, status, sender_name=None):
    status_lower = status.lower()
    color = "#22c55e" if "approve" in status_lower else "#ef4444"
    status_text = "APPROVED" if "approve" in status_lower else "REJECTED"
    desc = "Your travel request booking has been approved." if "approve" in status_lower else "Your travel request has been declined."
    content_html = f"""
    <p style="color:#ffffff;font-size:16px;">Your business travel booking request has been updated:</p>
    <div style="background-color:#1e293b;border-left:4px solid {color};padding:20px;border-radius:6px;margin-bottom:25px;">
      <table border="0" cellpadding="4" style="color:#94a3b8;font-size:14px;width:100%;">
        <tr><td style="font-weight:700;color:#ffffff;width:35%;">Destination:</td><td>{destination}</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Departure:</td><td>{departure_date}</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Return:</td><td>{return_date}</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Status:</td><td><strong style="color:{color};">{status_text}</strong></td></tr>
      </table>
    </div>
    <p style="color:#64748b;font-size:14px;">{desc}</p>
    """
    sender_suffix = f" by {sender_name}" if sender_name else ""
    return send_notification_email(to_email, employee_name, f"Business Travel Request {status_text}{sender_suffix} - {destination}", "Travel Notification", content_html, color)


def send_timesheet_status_email(to_email, employee_name, week_start, status, sender_name=None):
    status_lower = status.lower()
    color = "#22c55e" if "approve" in status_lower else "#ef4444"
    status_text = "APPROVED" if "approve" in status_lower else "REJECTED"
    desc = "Your logged timesheet has been successfully approved." if "approve" in status_lower else "Your weekly timesheet has been rejected. Please review and resubmit."
    content_html = f"""
    <p style="color:#ffffff;font-size:16px;">Your weekly timesheet status has been updated:</p>
    <div style="background-color:#1e293b;border-left:4px solid {color};padding:20px;border-radius:6px;margin-bottom:25px;">
      <table border="0" cellpadding="4" style="color:#94a3b8;font-size:14px;width:100%;">
        <tr><td style="font-weight:700;color:#ffffff;width:35%;">Week Starting:</td><td>{week_start}</td></tr>
        <tr><td style="font-weight:700;color:#ffffff;">Status:</td><td><strong style="color:{color};">{status_text}</strong></td></tr>
      </table>
    </div>
    <p style="color:#64748b;font-size:14px;">{desc}</p>
    """
    sender_suffix = f" by {sender_name}" if sender_name else ""
    return send_notification_email(to_email, employee_name, f"Timesheet {status_text}{sender_suffix} - Week {week_start}", "Timesheet Notification", content_html, color)


def send_recognition_email(to_email, employee_name, award_type, title, description, given_by_name):
    color = "#eab308"
    content_html = f"""
    <div style="text-align:center;margin-bottom:25px;">
      <span style="font-size:48px;">🏆</span>
      <h3 style="font-size:22px;font-weight:800;color:#eab308;margin-top:10px;">Spot Award Received!</h3>
      <p style="color:#94a3b8;font-size:14px;margin:0;">Award Category: <strong style="color:#ffffff;">{award_type}</strong></p>
    </div>
    <p style="color:#ffffff;font-size:16px;text-align:center;">Congratulations! <strong>{given_by_name}</strong> has recognized your contributions with:</p>
    <div style="background-color:#1e293b;border-top:4px solid {color};padding:20px;border-radius:6px;margin-bottom:25px;">
      <h4 style="font-size:16px;font-weight:700;color:#ffffff;text-align:center;">"{title}"</h4>
      <p style="color:#94a3b8;font-size:14px;text-align:center;">{description}</p>
    </div>
    """
    return send_notification_email(to_email, employee_name, f"Congratulations! You received a Spot Award from {given_by_name}: {award_type}", "Spot Recognition", content_html, color)


def send_announcement_email(to_email, employee_name, title, category, content):
    color = "#e8302a"
    content_html = f"""
    <div style="margin-bottom:20px;">
      <div style="display:inline-block;background-color:rgba(232,48,42,0.12);color:#e8302a;border:1px solid rgba(232,48,42,0.25);padding:4px 12px;border-radius:9999px;font-size:11px;font-weight:700;text-transform:uppercase;margin-bottom:15px;">📢 {category}</div>
      <h3 style="font-size:20px;font-weight:800;color:#ffffff;margin-top:5px;margin-bottom:15px;">{title}</h3>
    </div>
    <div style="background-color:#1e293b;border-left:4px solid {color};padding:20px;border-radius:6px;margin-bottom:25px;">
      <p style="color:#f5f5f5;font-size:14px;line-height:1.6;margin:0;">{content}</p>
    </div>
    <p style="color:#94a3b8;font-size:13px;">This is a company-wide announcement. Please log in to your employee portal for full details.</p>
    """
    return send_notification_email(to_email, employee_name, f"Company Announcement: {title}", "Company Announcement", content_html, color)
