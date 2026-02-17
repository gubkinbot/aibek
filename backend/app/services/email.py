import logging
from email.message import EmailMessage

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


async def send_verification_email(to_email: str, code: str) -> None:
    subject = "Код подтверждения - AI-платформа Узтрансгаз"
    body = (
        f"Ваш код подтверждения: {code}\n\n"
        f"Код действителен в течение 10 минут.\n\n"
        f"Если вы не запрашивали регистрацию, проигнорируйте это письмо."
    )

    if not settings.mail_enabled:
        logger.warning(f"[DEV MODE] Verification code for {to_email}: {code}")
        return

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.mail_smtp_host,
            port=settings.mail_smtp_port,
            use_tls=False,
            start_tls=False,
        )
        logger.info(f"Verification email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        raise


async def send_password_reset_email(to_email: str, code: str) -> None:
    subject = "Сброс пароля - AI-платформа Узтрансгаз"
    body = (
        f"Ваш код для сброса пароля: {code}\n\n"
        f"Код действителен в течение 10 минут.\n\n"
        f"Если вы не запрашивали сброс пароля, проигнорируйте это письмо."
    )

    if not settings.mail_enabled:
        logger.warning(f"[DEV MODE] Password reset code for {to_email}: {code}")
        return

    message = EmailMessage()
    message["From"] = settings.mail_from
    message["To"] = to_email
    message["Subject"] = subject
    message.set_content(body)

    try:
        await aiosmtplib.send(
            message,
            hostname=settings.mail_smtp_host,
            port=settings.mail_smtp_port,
            use_tls=False,
            start_tls=False,
        )
        logger.info(f"Password reset email sent to {to_email}")
    except Exception as e:
        logger.error(f"Failed to send password reset email to {to_email}: {e}")
        raise
