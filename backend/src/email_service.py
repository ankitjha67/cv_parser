"""
Email Service — SMTP-based with HTML templates.
Configurable via environment variables:
  SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, FROM_EMAIL
Falls back to console logging when SMTP is not configured.
"""
import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from typing import Optional
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=4)

# ── Config ────────────────────────────────────────────────────────────────────
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER or "noreply@cvmatcher.ai")
FROM_NAME = os.getenv("FROM_NAME", "CV Matcher Premium")
SMTP_ENABLED = bool(SMTP_HOST and SMTP_USER)


# ── Core sender ────────────────────────────────────────────────────────────────
def _send_sync(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Synchronous SMTP send — runs in thread pool."""
    if not SMTP_ENABLED:
        logger.info(f"[EMAIL-LOG] To={to_email} | Subject={subject}")
        logger.debug(f"[EMAIL-LOG] Body={text_body or html_body[:200]}")
        return True  # Treat as sent in dev mode

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
    msg["To"] = to_email
    msg["Date"] = formatdate(localtime=True)

    if text_body:
        msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, [to_email], msg.as_string())
        logger.info(f"Email sent → {to_email} | {subject}")
        return True
    except Exception as e:
        logger.error(f"Email failed → {to_email} | {e}")
        return False


async def send_email(to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
    """Async wrapper — runs SMTP in a thread pool executor."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor, _send_sync, to_email, subject, html_body, text_body
    )


# ── HTML Templates ─────────────────────────────────────────────────────────────
def _base_template(content: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
  body {{ margin:0; padding:0; background:#f4f4f0; font-family:'Georgia',serif; color:#1a1a1a; }}
  .wrapper {{ max-width:600px; margin:40px auto; background:#fff; border:1px solid #e0e0d8; }}
  .header {{ background:#1A4D3D; padding:32px 40px; }}
  .header h1 {{ margin:0; color:#fff; font-size:22px; letter-spacing:0.1em; font-family:Georgia,serif; }}
  .header p {{ margin:4px 0 0; color:#a8c5b8; font-size:11px; letter-spacing:0.2em; text-transform:uppercase; }}
  .body {{ padding:40px; }}
  .body h2 {{ font-size:20px; margin:0 0 16px; color:#1A4D3D; }}
  .body p {{ font-size:15px; line-height:1.7; color:#444; margin:0 0 16px; }}
  .highlight {{ background:#f0f7f4; border-left:3px solid #1A4D3D; padding:16px 20px; margin:24px 0; }}
  .highlight strong {{ color:#1A4D3D; }}
  .btn {{ display:inline-block; background:#E85D30; color:#fff; padding:12px 28px;
          text-decoration:none; font-size:13px; letter-spacing:0.15em; text-transform:uppercase;
          margin-top:24px; }}
  .score-badge {{ display:inline-block; background:#1A4D3D; color:#fff; padding:6px 16px;
                  font-size:28px; font-weight:bold; letter-spacing:0.05em; }}
  .gap-item {{ padding:6px 0; border-bottom:1px solid #f0f0e8; font-size:14px; color:#555; }}
  .footer {{ background:#f9f9f7; padding:20px 40px; border-top:1px solid #e0e0d8; }}
  .footer p {{ margin:0; font-size:11px; color:#999; letter-spacing:0.05em; }}
</style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>CV Matcher</h1>
    <p>Premium · Intelligent Career Platform</p>
  </div>
  <div class="body">{content}</div>
  <div class="footer">
    <p>© {datetime.now().year} CV Matcher Premium. You are receiving this because you are registered on our platform.</p>
  </div>
</div>
</body>
</html>"""


# ── Specific email builders ────────────────────────────────────────────────────

async def send_welcome_email(to_email: str, name: str) -> bool:
    subject = "Welcome to CV Matcher Premium"
    content = f"""
<h2>Welcome, {name}</h2>
<p>Your account has been created. You can now upload your CV, match against job descriptions, and generate tailored applications — all in one place.</p>
<div class="highlight">
  <strong>What to do next:</strong><br>
  Upload your CV → Add job descriptions → Run matching → Download tailored CV
</div>
<a class="btn" href="#">Open Dashboard</a>"""
    text = f"Welcome {name}! Your CV Matcher Premium account is ready."
    return await send_email(to_email, subject, _base_template(content, subject), text)


async def send_status_change_email(
    to_email: str, candidate_name: str,
    company: str, position: str, new_status: str, notes: str = ""
) -> bool:
    status_messages = {
        "screening": "Your application has moved to the <strong>Screening</strong> stage.",
        "interview": "Congratulations! You have been selected for an <strong>Interview</strong>.",
        "offer": "Excellent news — you have received an <strong>Offer</strong>!",
        "accepted": "Your offer has been <strong>Accepted</strong>. Congratulations!",
        "rejected": "Unfortunately, your application was not successful this time.",
        "withdrawn": "Your application has been marked as <strong>Withdrawn</strong>.",
    }
    status_text = status_messages.get(new_status, f"Status updated to <strong>{new_status}</strong>.")
    subject = f"Application Update — {position} at {company}"
    content = f"""
<h2>Application Status Update</h2>
<p>Dear {candidate_name},</p>
<p>There has been an update to your application for <strong>{position}</strong> at <strong>{company}</strong>.</p>
<div class="highlight">{status_text}</div>
{"<p><strong>Recruiter Notes:</strong> " + notes + "</p>" if notes else ""}
<p>Log in to your dashboard to view full details and next steps.</p>"""
    text = f"Application update for {position} at {company}: {new_status}"
    return await send_email(to_email, subject, _base_template(content, subject), text)


async def send_match_notification_email(
    to_email: str, name: str,
    jd_title: str, score: float, hard_gaps: list
) -> bool:
    subject = f"New Match Result — {jd_title} ({score:.0f}/100)"
    gaps_html = "".join(f'<div class="gap-item">· {g}</div>' for g in hard_gaps[:5])
    content = f"""
<h2>Your Match Results Are Ready</h2>
<p>Dear {name},</p>
<p>We have analysed your CV against <strong>{jd_title}</strong>. Here is your ATS score:</p>
<p><span class="score-badge">{score:.0f}<small style="font-size:14px">/100</small></span></p>
{"<div class='highlight'><strong>Key gaps to address:</strong>" + gaps_html + "</div>" if hard_gaps else ""}
<p>Log in to generate your tailored CV and interview prep materials.</p>"""
    text = f"Match result for {jd_title}: {score:.0f}/100"
    return await send_email(to_email, subject, _base_template(content, subject), text)


async def send_interview_invitation_email(
    to_email: str, candidate_name: str,
    position: str, company: str,
    scheduled_at: datetime, duration_minutes: int,
    location: str = "", meeting_link: str = "",
    recruiter_name: str = "", notes: str = ""
) -> bool:
    dt_str = scheduled_at.strftime("%A, %d %B %Y at %I:%M %p")
    location_html = f"<p><strong>Location:</strong> {location}</p>" if location else ""
    link_html = f'<p><strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a></p>' if meeting_link else ""
    subject = f"Interview Invitation — {position} at {company}"
    content = f"""
<h2>Interview Invitation</h2>
<p>Dear {candidate_name},</p>
<p>You have been invited for an interview for the position of <strong>{position}</strong> at <strong>{company}</strong>.</p>
<div class="highlight">
  <strong>Date & Time:</strong> {dt_str}<br>
  <strong>Duration:</strong> {duration_minutes} minutes
  {("<br><strong>Location:</strong> " + location) if location else ""}
  {("<br><strong>Meeting Link:</strong> " + meeting_link) if meeting_link else ""}
</div>
{location_html}{link_html}
{"<p><strong>Notes:</strong> " + notes + "</p>" if notes else ""}
{"<p>Your interviewer will be <strong>" + recruiter_name + "</strong>.</p>" if recruiter_name else ""}
<p>A calendar invite (.ics) has been attached. Please confirm your attendance by logging into your dashboard.</p>"""
    text = f"Interview scheduled for {position} at {company} on {dt_str}"
    return await send_email(to_email, subject, _base_template(content, subject), text)


async def send_interview_reminder_email(
    to_email: str, candidate_name: str,
    position: str, company: str,
    scheduled_at: datetime, meeting_link: str = ""
) -> bool:
    dt_str = scheduled_at.strftime("%A, %d %B %Y at %I:%M %p")
    subject = f"Interview Reminder — Tomorrow: {position} at {company}"
    content = f"""
<h2>Interview Reminder</h2>
<p>Dear {candidate_name},</p>
<p>This is a reminder that you have an interview scheduled for <strong>tomorrow</strong>.</p>
<div class="highlight">
  <strong>Position:</strong> {position} at {company}<br>
  <strong>Time:</strong> {dt_str}
  {("<br><strong>Link:</strong> " + meeting_link) if meeting_link else ""}
</div>
<p>Make sure to review your tailored CV and interview preparation materials before the session.</p>"""
    text = f"Reminder: Interview tomorrow for {position} at {company} at {dt_str}"
    return await send_email(to_email, subject, _base_template(content, subject), text)
