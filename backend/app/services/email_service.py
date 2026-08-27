import logging
from typing import Dict, Any, Optional
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

        accept_url = f"{self.frontend_url}/accept-invite?token={token}"
        role_title = role.capitalize()

        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Join {company_name} on Datalyze</title>
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
        <h1>You're invited to join {company_name}</h1>
        <p>Hello <strong>{recipient_name or 'there'}</strong>,</p>
        <p>
          <strong>{inviter_name}</strong> has invited you to collaborate in the <strong>{company_name}</strong> workspace on Datalyze.
        </p>

        <div class="badge-box">
          <table style="width:100%; border-collapse: collapse; font-size: 13px;">
            <tr>
              <td style="color:#7A7A7A; padding: 4px 0;">Workspace:</td>
              <td style="font-weight:600; text-align:right; color:#1A1A1A;">{company_name}</td>
            </tr>
            <tr>
              <td style="color:#7A7A7A; padding: 4px 0;">Assigned Role:</td>
              <td style="font-weight:600; text-align:right; color:#6B4226;">{role_title}</td>
            </tr>
            <tr>
              <td style="color:#7A7A7A; padding: 4px 0;">Email:</td>
              <td style="font-weight:600; text-align:right; color:#1A1A1A;">{to_email}</td>
            </tr>
          </table>
        </div>

        <div class="btn-container">
          <a href="{accept_url}" class="btn" target="_blank">Accept Invitation & Set Password</a>
        </div>

        <p style="font-size: 12px; color: #7A7A7A; text-align: center;">
          ⏱️ This invitation link will expire in <strong>7 days</strong>.
        </p>

        <div class="fallback-box">
          <strong>Button not working?</strong> Copy and paste this link into your browser:<br>
          <a href="{accept_url}" style="color:#6B4226;">{accept_url}</a>
        </div>
      </div>
      <div class="footer">
        If you did not expect an invitation from {company_name}, you can safely ignore this email.<br>
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
            params = {
                "from": self.from_email,
                "to": [to_email],
                "subject": f"You're invited to join {company_name} on Datalyze",
                "html": html_content,
                "text": text_content,
            }
            logger.info(f"Sending invitation email to {to_email} via Resend from {self.from_email}...")
            response = resend.Emails.send(params)

            # Response is typically a dictionary like {'id': '...'}
            email_id = response.get("id") if isinstance(response, dict) else getattr(response, "id", str(response))
            logger.info(f"Resend email dispatched successfully! Email ID: {email_id}")

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
                "to": to_email,
                "accept_url": accept_url
            }

        except Exception as exc:
            err_str = str(exc)
            logger.error(f"Resend API error sending email to {to_email}: {err_str}", exc_info=True)
            log_audit_event(
                event="resend_invitation_email_failed",
                details={"to": to_email, "error": err_str},
                level="ERROR",
                status="FAILURE"
            )
            if "testing emails to your own email address" in err_str.lower():
                raise DataValidationException(
                    f"Resend Sandbox Notice: On the free tier (onboarding@resend.dev), invitations can only be delivered to your registered email (revanthjoshua77@gmail.com). To send to '{to_email}', please verify a custom domain at resend.com/domains."
                )
            raise DataValidationException(f"Failed to deliver invitation email via Resend: {err_str}")



email_service = EmailService()
