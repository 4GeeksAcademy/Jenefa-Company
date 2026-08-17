"""Transactional email dispatch for password-reset links.

API keys are loaded exclusively from environment variables (never hardcoded).
Supports Resend or SendGrid; falls back to console logging when no provider key is set
so local development can still exercise the token pipeline.
"""

from __future__ import annotations

import logging
import sys
from urllib.parse import quote

import httpx

from .config import get_settings

logger = logging.getLogger(__name__)


class EmailDispatchError(Exception):
    """Raised when a third-party mail provider cannot complete a send."""


def build_reset_link(token: str) -> str:
    settings = get_settings()
    return f"{settings.frontend_base_url}/reset-password?token={quote(token, safe='')}"


def send_password_reset_email(to_email: str, token: str) -> None:
    """Send a functional reset link to a registered address."""
    settings = get_settings()
    reset_link = build_reset_link(token)
    subject = "HealthCore password reset"
    text_body = (
        "You requested a password reset for your HealthCore staff account.\n\n"
        f"Open this link to choose a new password (expires soon):\n{reset_link}\n\n"
        "If you did not request this, you can ignore this email."
    )
    html_body = (
        "<p>You requested a password reset for your HealthCore staff account.</p>"
        f'<p><a href="{reset_link}">Reset your password</a></p>'
        "<p>If you did not request this, you can ignore this email.</p>"
    )

    provider = settings.email_provider
    if not provider:
        if settings.resend_api_key:
            provider = "resend"
        elif settings.sendgrid_api_key:
            provider = "sendgrid"
        else:
            provider = "console"

    if provider == "resend":
        _send_via_resend(to_email, subject, text_body, html_body)
    elif provider == "sendgrid":
        _send_via_sendgrid(to_email, subject, text_body, html_body)
    else:
        # Local-only recovery path: do not attach recipient email to the token line.
        logger.info("password_reset_email console fallback dispatched")
        print(f"Password reset link: {reset_link}", file=sys.stderr)


def _send_via_resend(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    settings = get_settings()
    if not settings.resend_api_key:
        raise EmailDispatchError("RESEND_API_KEY is not set")
    try:
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "from": settings.email_from,
                "to": [to_email],
                "subject": subject,
                "text": text_body,
                "html": html_body,
            },
            timeout=20.0,
        )
    except httpx.TimeoutException as exc:
        logger.error("Resend request timed out")
        raise EmailDispatchError("Email provider timed out") from exc
    except httpx.RequestError as exc:
        logger.error("Resend request failed")
        raise EmailDispatchError("Email provider is unavailable") from exc
    if response.status_code >= 400:
        logger.error("Resend dispatch failed: status=%s", response.status_code)
        raise EmailDispatchError("Email provider rejected the message")


def _send_via_sendgrid(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    settings = get_settings()
    if not settings.sendgrid_api_key:
        raise EmailDispatchError("SENDGRID_API_KEY is not set")
    try:
        response = httpx.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {settings.sendgrid_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": _parse_from_email(settings.email_from)},
                "subject": subject,
                "content": [
                    {"type": "text/plain", "value": text_body},
                    {"type": "text/html", "value": html_body},
                ],
            },
            timeout=20.0,
        )
    except httpx.TimeoutException as exc:
        logger.error("SendGrid request timed out")
        raise EmailDispatchError("Email provider timed out") from exc
    except httpx.RequestError as exc:
        logger.error("SendGrid request failed")
        raise EmailDispatchError("Email provider is unavailable") from exc
    if response.status_code >= 400:
        logger.error("SendGrid dispatch failed: status=%s", response.status_code)
        raise EmailDispatchError("Email provider rejected the message")


def _parse_from_email(from_header: str) -> str:
    """Extract bare email from `Name <email@x>` or plain address."""
    if "<" in from_header and ">" in from_header:
        return from_header.split("<", 1)[1].split(">", 1)[0].strip()
    return from_header.strip()
