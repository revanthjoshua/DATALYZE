import hashlib
from datetime import datetime, timezone, timedelta

import pytest
import resend

from app.core.exceptions import DatalyzeException
from app.models.company import Company
from app.models.invitation import Invitation
from app.models.user import User
from app.services.email_service import email_service
from app.services.invitation_service import InvitationService


@pytest.fixture
def admin(db_session):
    company = Company(name="Email test workspace")
    db_session.add(company)
    db_session.flush()
    user = User(company_id=company.id, email="admin@example.test", username="admin", full_name="Admin",
                hashed_password="unused", role="admin")
    db_session.add(user)
    db_session.commit()
    return user


def test_failed_new_invitation_is_not_saved(db_session, admin, monkeypatch):
    monkeypatch.setattr(email_service, "api_key", "")
    service = InvitationService(db_session, admin.company_id)
    with pytest.raises(DatalyzeException) as error:
        service.create_or_renew_invitation("new@example.test", inviter_user=admin)
    assert error.value.status_code == 502
    assert db_session.query(Invitation).count() == 0


@pytest.mark.parametrize("resend_existing", [False, True])
def test_failed_renewal_preserves_old_link(db_session, admin, monkeypatch, resend_existing):
    service = InvitationService(db_session, admin.company_id)
    invitation = service.create_or_renew_invitation("member@example.test", role="viewer", inviter_user=admin)
    original_token, original_expiry = invitation.token, invitation.expires_at
    monkeypatch.setattr(resend.Emails, "send", lambda params: {})
    with pytest.raises(DatalyzeException):
        if resend_existing:
            service.resend_invitation(invitation.id, admin)
        else:
            service.create_or_renew_invitation("member@example.test", role="admin", inviter_user=admin)
    db_session.refresh(invitation)
    assert invitation.token == original_token
    assert invitation.expires_at == original_expiry
    assert invitation.role == "viewer"
    assert invitation.status == "pending"


def test_provider_response_requires_acceptance_id_and_escapes_html(monkeypatch):
    sent = []
    monkeypatch.setattr(resend.Emails, "send", lambda params: sent.append(params) or {})
    result = email_service.send_invitation_email(
        to_email="member@example.test", recipient_name="<b>Member</b>", company_name="<script>bad</script>",
        inviter_name="Admin", role="viewer", token="token&injected=1"
    )
    assert result["success"] is False
    assert "<script>bad</script>" not in sent[0]["html"]
    assert "&lt;script&gt;bad&lt;/script&gt;" in sent[0]["html"]
    assert "<b>Member</b>" not in sent[0]["html"]
    assert "&lt;b&gt;Member&lt;/b&gt;" in sent[0]["html"]
    assert "token%26injected%3D1" in sent[0]["html"]


def test_failed_reset_preserves_previous_code(db_session, admin, monkeypatch):
    from app.models.password_reset_code import PasswordResetCode
    from app.schemas.user_schema import ForgotPasswordRequest
    from app.services.auth_service import AuthService

    previous = PasswordResetCode(user_id=admin.id, target=admin.email,
        code=hashlib.sha256(b"123456").hexdigest(), expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        is_used=False)
    db_session.add(previous)
    db_session.commit()
    monkeypatch.setattr(email_service, "send_password_reset_otp_email", lambda **kwargs: {"success": False})
    service = AuthService(db_session)
    with pytest.raises(DatalyzeException) as error:
        service.request_password_reset(ForgotPasswordRequest(identifier=admin.email, portal_type="admin"))
    assert error.value.status_code == 502
    db_session.refresh(previous)
    assert previous.is_used is False
    assert db_session.query(PasswordResetCode).count() == 1


def test_provider_failures_do_not_expose_request_secrets(monkeypatch, caplog):
    secret = "example-secret-request-token"

    def fail_send(params):
        raise RuntimeError(secret)

    monkeypatch.setattr(resend.Emails, "send", fail_send)
    invitation = email_service.send_invitation_email(
        to_email="member@example.test", recipient_name="Member", company_name="Workspace",
        inviter_name="Admin", role="viewer", token=secret,
    )
    reset = email_service.send_password_reset_otp_email(
        to_email="member@example.test", recipient_name="Member", otp_code="654321",
    )
    assert not invitation["success"] and not reset["success"]
    assert secret not in str(invitation) + str(reset) + caplog.text


def test_invitation_cannot_use_an_admin_from_another_tenant(db_session, admin):
    other_company = Company(name="Other workspace")
    db_session.add(other_company)
    db_session.commit()
    with pytest.raises(DatalyzeException) as error:
        InvitationService(db_session, other_company.id).create_or_renew_invitation(
            "member@example.test", inviter_user=admin,
        )
    assert error.value.status_code == 403
    assert db_session.query(Invitation).count() == 0
