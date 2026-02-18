import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings
from app.services.email_templates import (
    _TRANSLATIONS,
    _t,
    password_reset_email_html,
    verification_email_html,
)

logger = logging.getLogger(__name__)


async def _send(message: EmailMessage) -> None:
    await aiosmtplib.send(
        message,
        hostname=settings.mail_smtp_host,
        port=settings.mail_smtp_port,
        use_tls=False,
        start_tls=False,
    )


def _normalize_lang(lang: str) -> str:
    lang = (lang or "ru").strip().lower()[:2]
    return lang if lang in _TRANSLATIONS else "ru"


async def send_verification_email(to_email: str, code: str, lang: str = "ru") -> None:
    lang = _normalize_lang(lang)
    subject = _t(lang, "verify_subject")
    plain = _t(lang, "verify_plain", code=code)

    if not settings.mail_enabled:
        logger.warning(f"[DEV MODE] Verification code for {to_email}: {code}")
        return

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain)
    message.add_alternative(verification_email_html(code, lang=lang), subtype="html")

    try:
        await _send(message)
        logger.info(f"Verification email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise


async def send_password_reset_email(to_email: str, code: str, lang: str = "ru") -> None:
    lang = _normalize_lang(lang)
    subject = _t(lang, "reset_subject")
    plain = _t(lang, "reset_plain", code=code)

    if not settings.mail_enabled:
        logger.warning(f"[DEV MODE] Password reset code for {to_email}: {code}")
        return

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(plain)
    message.add_alternative(password_reset_email_html(code, lang=lang), subtype="html")

    try:
        await _send(message)
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        raise
