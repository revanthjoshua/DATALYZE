import logging
from html import escape
from urllib.parse import urlencode
from typing import Dict, Any
import resend
from app.core.config import settings
from app.core.exceptions import DataValidationException
from app.core.logging import log_audit_event

logger = logging.getLogger("datalyze.email")


class EmailService:
    """
    Transactional Email Service powered by Resend SDK.
    Dispatches invitation and notification emails with modern Datalyze styling.
    """

    def __init__(self):
        self.api_key = settings.RESEND_API_KEY
        self.from_email = settings.RESEND_FROM_EMAIL
        self.frontend_url = settings.FRONTEND_URL.rstrip("/")
        if self.api_key:
            resend.api_key = self.api_key

    def _get_formatted_from(self) -> str:
        sender = (self.from_email or "Datalyze <onboarding@resend.dev>").strip()
        if "@" in sender and "<" not in sender and " " in sender:
            parts = sender.rsplit(" ", 1)
            if "@" in parts[1]:
                return f"{parts[0]} <{parts[1]}>"
        return sender

    def send_invitation_email(
        self,
        to_email: str,
        recipient_name: str,
        company_name: str,
        inviter_name: str,
        role: str,
        token: str,
    ) -> Dict[str, Any]:
        """
        Sends a branded workspace team invitation email via Resend.
        """
        if not self.api_key:
            err_msg = "Resend API key is not configured. Please set RESEND_API_KEY in backend/.env."
            logger.error(err_msg)
            raise DataValidationException(err_msg)

        accept_url = f"{self.frontend_url}/accept-invite?{urlencode({'token': token})}"
        role_title = role.capitalize()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Join {escape(company_name, quote=True)} on Datalyze</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #FAF8F5;
      color: #1A1A1A;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      width: 100%;
      table-layout: fixed;
      background-color: #FAF8F5;
      padding: 40px 16px;
    }}
    .container {{
      max-width: 560px;
      margin: 0 auto;
      background: #FFFFFF;
      border: 1px solid #E5DFD7;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(107, 66, 38, 0.06);
    }}
    .header {{
      background: linear-gradient(135deg, #4A2E1B 0%, #6B4226 100%);
      padding: 32px 32px 24px;
      text-align: center;
      color: #FFFFFF;
    }}
    .logo {{
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 2px;
      color: #F4ECE4;
      text-transform: uppercase;
      margin-bottom: 4px;
    }}
    .subtitle {{
      font-size: 12px;
      color: #D5B79F;
      font-weight: 500;
      letter-spacing: 0.5px;
    }}
    .body {{
      padding: 36px 32px;
    }}
    h1 {{
      font-size: 20px;
      font-weight: 700;
      color: #1A1A1A;
      margin: 0 0 16px;
    }}
    p {{
      font-size: 14px;
      line-height: 1.6;
      color: #4A4A4A;
      margin: 0 0 18px;
    }}
    .badge-box {{
      background: #FAF8F5;
      border: 1px solid #EAE4DC;
      border-radius: 12px;
      padding: 16px;
      margin: 20px 0 24px;
    }}
    .badge-row {{
      display: flex;
      justify-content: space-between;
      margin-bottom: 8px;
      font-size: 13px;
    }}
    .badge-label {{
      color: #7A7A7A;
      font-weight: 500;
    }}
    .badge-value {{
      color: #1A1A1A;
      font-weight: 600;
    }}
    .btn-container {{
      text-align: center;
      margin: 32px 0 24px;
    }}
    .btn {{
      display: inline-block;
      background: #6B4226;
      color: #FFFFFF !important;
      text-decoration: none;
      padding: 14px 32px;
      font-size: 14px;
      font-weight: 600;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(107, 66, 38, 0.25);
    }}
    .fallback-box {{
      background: #F5F3EF;
      border-radius: 8px;
      padding: 12px;
      font-size: 11px;
      color: #6B6B6B;
      word-break: break-all;
      margin-top: 24px;
    }}
    .footer {{
      padding: 20px 32px;
      border-top: 1px solid #F0ECE6;
      background: #FAF8F5;
      text-align: center;
      font-size: 12px;
      color: #8C8C8C;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <div class="logo">DATALYZE</div>
        <div class="subtitle">DECISION INTELLIGENCE PLATFORM</div>
      </div>
      <div class="body">
        <h1>You're invited to join {escape(company_name, quote=True)}</h1>
        <p>Hello <strong>{escape(recipient_name or 'there', quote=True)}</strong>,</p>
        <p>
          <strong>{escape(inviter_name, quote=True)}</strong> has invited you to collaborate in the <strong>{escape(company_name, quote=True)}</strong> workspace on Datalyze.
        </p>

        <div class="badge-box">
          <table style="width:100%; border-collapse: collapse; font-size: 13px;">
            <tr>
              <td style="color:#7A7A7A; padding: 4px 0;">Workspace:</td>
              <td style="font-weight:600; text-align:right; color:#1A1A1A;">{escape(company_name, quote=True)}</td>
            </tr>
            <tr>
              <td style="color:#7A7A7A; padding: 4px 0;">Assigned Role:</td>
              <td style="font-weight:600; text-align:right; color:#6B4226;">{escape(role_title, quote=True)}</td>
            </tr>
            <tr>
              <td style="color:#7A7A7A; padding: 4px 0;">Email:</td>
              <td style="font-weight:600; text-align:right; color:#1A1A1A;">{escape(to_email, quote=True)}</td>
            </tr>
          </table>
        </div>

        <div class="btn-container">
          <a href="{escape(accept_url, quote=True)}" class="btn" target="_blank">Accept Invitation & Set Password</a>
        </div>

        <p style="font-size: 12px; color: #7A7A7A; text-align: center;">
          ⏱️ This invitation link will expire in <strong>7 days</strong>.
        </p>

        <div class="fallback-box">
          <strong>Button not working?</strong> Copy and paste this link into your browser:<br>
          <a href="{escape(accept_url, quote=True)}" style="color:#6B4226;">{escape(accept_url, quote=True)}</a>
        </div>
      </div>
      <div class="footer">
        If you did not expect an invitation from {escape(company_name, quote=True)}, you can safely ignore this email.<br>
        &copy; 2026 Datalyze Inc. All rights reserved.
      </div>
    </div>
  </div>
</body>
</html>
"""

        text_content = f"""
You're invited to join {company_name} on Datalyze!

Hello {recipient_name or 'there'},

{inviter_name} has invited you to collaborate in the {company_name} workspace on Datalyze as {role_title}.

To accept this invitation and create your account, visit:
{accept_url}

This invitation link expires in 7 days.

If you did not expect this invitation, you can safely ignore this email.
"""

        try:
            resend.api_key = self.api_key
            sender = self._get_formatted_from()
            params = {
                "from": sender,
                "to": [to_email],
                "subject": f"You're invited to join {company_name} on Datalyze",
                "html": html_content,
                "text": text_content,
            }
            logger.info(f"Sending invitation email to {to_email} via Resend from {sender}...")
            response = resend.Emails.send(params)

            # Response is typically a dictionary like {'id': '...'}
            email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
            if not email_id:
                raise RuntimeError("Email provider did not return an acceptance ID")
            logger.info(f"Resend email accepted! Email ID: {email_id}")

            log_audit_event(
                event="resend_invitation_email_sent",
                details={
                    "to": to_email,
                    "company_name": company_name,
                    "role": role,
                    "email_id": email_id
                },
                level="INFO",
                status="SUCCESS"
            )

            return {
                "success": True,
                "email_id": email_id,
                "to": to_email
            }

        except Exception as exc:
            error_type = type(exc).__name__
            logger.error("Invitation email provider failure (%s)", error_type)
            log_audit_event(
                event="resend_invitation_email_failed",
                details={"to": to_email, "error_type": error_type},
                level="ERROR",
                status="FAILURE"
            )
            return {
                "success": False,
                "error": "The email provider did not accept the invitation.",
                "to": to_email
            }

    def send_password_reset_otp_email(
        self,
        to_email: str,
        recipient_name: str,
        otp_code: str,
        expires_in_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Sends a branded password reset verification code email via Resend.
        """
        if not self.api_key:
            logger.warning("Resend API key is not configured. Password reset email skipped.")
            return {"success": False, "message": "Resend API key not configured"}

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reset Your Datalyze Password</title>
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #FAF8F5;
      color: #1A1A1A;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      max-width: 600px;
      margin: 40px auto;
      background-color: #FFFFFF;
      border-radius: 16px;
      overflow: hidden;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
      border: 1px solid #EAE5DE;
    }}
    .header {{
      background: linear-gradient(135deg, #1C1917 0%, #292524 100%);
      padding: 32px 40px;
      text-align: center;
    }}
    .logo-text {{
      color: #FFFFFF;
      font-size: 24px;
      font-weight: 800;
      letter-spacing: -0.5px;
      margin: 0;
    }}
    .tagline {{
      color: #A8A29E;
      font-size: 13px;
      margin-top: 4px;
      text-transform: uppercase;
      letter-spacing: 1px;
    }}
    .content {{
      padding: 40px;
    }}
    .otp-card {{
      background-color: #F8FAFC;
      border: 2px dashed #CBD5E1;
      border-radius: 12px;
      padding: 24px;
      text-align: center;
      margin: 28px 0;
    }}
    .otp-code {{
      font-family: 'Courier New', Courier, monospace;
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 8px;
      color: #0F172A;
      margin: 8px 0;
    }}
    .footer {{
      background-color: #FAF8F5;
      border-top: 1px solid #EAE5DE;
      padding: 24px 40px;
      text-align: center;
      font-size: 12px;
      color: #78716C;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1 class="logo-text">DATALYZE</h1>
      <div class="tagline">Decision Intelligence Platform</div>
    </div>
    <div class="content">
      <h2 style="font-size: 20px; font-weight: 700; margin-top: 0; color: #1C1917;">Password Reset Verification</h2>
      <p style="font-size: 15px; line-height: 1.6; color: #44403C;">
        Hello <strong>{escape(recipient_name or 'there', quote=True)}</strong>,
      </p>
      <p style="font-size: 15px; line-height: 1.6; color: #44403C;">
        We received a request to reset your Datalyze password. Use the single-use verification code below to authorize your password change:
      </p>
      <div class="otp-card">
        <div style="font-size: 12px; color: #64748B; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Your 6-Digit Verification Code</div>
        <div class="otp-code">{escape(otp_code, quote=True)}</div>
        <div style="font-size: 13px; color: #64748B;">Expires in {expires_in_minutes} minutes</div>
      </div>
      <p style="font-size: 14px; line-height: 1.6; color: #78716C;">
        If you did not request this password reset, please ignore this message. Your password will remain unchanged and your account remains secure.
      </p>
    </div>
    <div class="footer">
      &copy; Datalyze Inc. Secure Enterprise Decision Intelligence.
    </div>
  </div>
</body>
</html>
        """

        text_content = f"""
DATALYZE - Password Reset Verification

Hello {recipient_name or 'there'},

We received a request to reset your Datalyze password. Your single-use 6-digit verification code is:

{otp_code}

This code will expire in {expires_in_minutes} minutes.

If you did not request a password reset, you can safely ignore this email.
"""

        try:
            resend.api_key = self.api_key
            sender = self._get_formatted_from()
            params = {
                "from": sender,
                "to": [to_email],
                "subject": f"Your Datalyze Verification Code: {otp_code}",
                "html": html_content,
                "text": text_content,
            }
            logger.info(f"Sending password reset OTP email to {to_email} via Resend from {sender}...")
            response = resend.Emails.send(params)
            email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", None)
            if not email_id:
                raise RuntimeError("Email provider did not return an acceptance ID")
            logger.info(f"Resend OTP email accepted! ID: {email_id}")
            log_audit_event(
                event="resend_password_reset_email_sent",
                details={"to": to_email, "email_id": email_id},
                level="INFO",
                status="SUCCESS"
            )
            return {"success": True, "email_id": email_id, "to": to_email}
        except Exception as exc:
            error_type = type(exc).__name__
            logger.error("Password reset email provider failure (%s)", error_type)
            log_audit_event(
                event="resend_password_reset_email_failed",
                details={"to": to_email, "error_type": error_type},
                level="ERROR",
                status="FAILURE"
            )
            return {"success": False, "error": "The email provider did not accept the verification code."}



email_service = EmailService()

