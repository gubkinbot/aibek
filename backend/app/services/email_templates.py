_TRANSLATIONS = {
    "ru": {
        "brand": "AI-платформа Узтрансгаз",
        "footer_auto": "Это автоматическое сообщение от AI-платформы Узтрансгаз.",
        "footer_noreply": "Пожалуйста, не отвечайте на это письмо.",
        "verify_subject": "Код подтверждения - AI-платформа Узтрансгаз",
        "verify_title": "Подтверждение email",
        "verify_desc": "Используйте код ниже для подтверждения вашего адреса электронной почты.",
        "verify_preheader": "Ваш код подтверждения: {code}",
        "verify_plain": "Ваш код подтверждения: {code}\n\nКод действителен в течение 10 минут.\n\nЕсли вы не запрашивали регистрацию, проигнорируйте это письмо.",
        "verify_ignore": "Если вы не запрашивали регистрацию, проигнорируйте это письмо.",
        "reset_subject": "Сброс пароля - AI-платформа Узтрансгаз",
        "reset_title": "Сброс пароля",
        "reset_desc": "Используйте код ниже для сброса пароля вашей учётной записи.",
        "reset_preheader": "Ваш код для сброса пароля: {code}",
        "reset_plain": "Ваш код для сброса пароля: {code}\n\nКод действителен в течение 10 минут.\n\nЕсли вы не запрашивали сброс пароля, проигнорируйте это письмо.",
        "reset_ignore": "Если вы не запрашивали сброс пароля, проигнорируйте это письмо.",
        "code_valid": "Код действителен <strong style=\"color:#6b7280;\">10 минут</strong>.",
    },
    "uz": {
        "brand": "AI-platforma O'ztransgaz",
        "footer_auto": "Bu AI-platforma O'ztransgaz tomonidan avtomatik yuborilgan xabar.",
        "footer_noreply": "Iltimos, bu xatga javob bermang.",
        "verify_subject": "Tasdiqlash kodi - AI-platforma O'ztransgaz",
        "verify_title": "Emailni tasdiqlash",
        "verify_desc": "Elektron pochta manzilingizni tasdiqlash uchun quyidagi kodni kiriting.",
        "verify_preheader": "Sizning tasdiqlash kodingiz: {code}",
        "verify_plain": "Sizning tasdiqlash kodingiz: {code}\n\nKod 10 daqiqa davomida amal qiladi.\n\nAgar siz ro'yxatdan o'tishni so'ramagan bo'lsangiz, bu xatni e'tiborsiz qoldiring.",
        "verify_ignore": "Agar siz ro'yxatdan o'tishni so'ramagan bo'lsangiz, bu xatni e'tiborsiz qoldiring.",
        "reset_subject": "Parolni tiklash - AI-platforma O'ztransgaz",
        "reset_title": "Parolni tiklash",
        "reset_desc": "Hisobingiz parolini tiklash uchun quyidagi kodni kiriting.",
        "reset_preheader": "Parolni tiklash kodingiz: {code}",
        "reset_plain": "Parolni tiklash kodingiz: {code}\n\nKod 10 daqiqa davomida amal qiladi.\n\nAgar siz parolni tiklashni so'ramagan bo'lsangiz, bu xatni e'tiborsiz qoldiring.",
        "reset_ignore": "Agar siz parolni tiklashni so'ramagan bo'lsangiz, bu xatni e'tiborsiz qoldiring.",
        "code_valid": "Kod <strong style=\"color:#6b7280;\">10 daqiqa</strong> davomida amal qiladi.",
    },
}


def _t(lang: str, key: str, **kwargs: str) -> str:
    text = _TRANSLATIONS.get(lang, _TRANSLATIONS["ru"])[key]
    return text.format(**kwargs) if kwargs else text


def _base_template(content: str, preheader: str = "", lang: str = "ru") -> str:
    """Wrap content block in the shared email shell."""
    brand = _t(lang, "brand")
    footer_auto = _t(lang, "footer_auto")
    footer_noreply = _t(lang, "footer_noreply")

    return f"""\
<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<meta name="color-scheme" content="light dark"/>
<meta name="supported-color-schemes" content="light dark"/>
<title>{brand}</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ margin:0; padding:0; background-color:#f3f4f6; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background-color:#111827 !important; }}
    .outer-card {{ background-color:#1f2937 !important; border-color:#374151 !important; }}
    .header-bg {{ background-color:#1e40af !important; background:linear-gradient(135deg,#1e40af,#6d28d9) !important; }}
    .body-text {{ color:#d1d5db !important; }}
    .code-box {{ background-color:#111827 !important; border-color:#4f46e5 !important; color:#a5b4fc !important; }}
    .footer-text {{ color:#6b7280 !important; }}
    .divider {{ border-color:#374151 !important; }}
  }}
</style>
</head>
<body style="margin:0;padding:0;background-color:#f3f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;">
  <!--[if !mso]><!-->
  <div style="display:none;max-height:0;overflow:hidden;">{preheader}</div>
  <!--<![endif]-->
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color:#f3f4f6;">
    <tr><td align="center" style="padding:40px 16px;">
      <table role="presentation" class="outer-card" width="480" cellspacing="0" cellpadding="0" border="0" style="max-width:480px;width:100%;background-color:#ffffff;border-radius:16px;border:1px solid #e5e7eb;overflow:hidden;">

        <!-- Header -->
        <tr><td class="header-bg" bgcolor="#2563eb" style="background-color:#2563eb;background:linear-gradient(135deg,#2563eb,#7c3aed);padding:16px 32px;text-align:center;">
        </td></tr>

        <!-- Body -->
        <tr><td style="padding:32px;">
          {content}
        </td></tr>

        <!-- Footer -->
        <tr><td style="padding:0 32px 28px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
            <tr><td class="divider" style="border-top:1px solid #e5e7eb;padding-top:20px;">
              <p class="footer-text" style="margin:0;font-size:12px;color:#9ca3af;line-height:1.6;text-align:center;">
                {footer_auto}<br/>
                {footer_noreply}
              </p>
            </td></tr>
          </table>
        </td></tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def _code_block(code: str) -> str:
    return f"""\
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
  <tr><td align="center">
    <table role="presentation" cellspacing="0" cellpadding="0" border="0">
      <tr><td class="code-box" style="background-color:#f0f0ff;border:2px dashed #818cf8;border-radius:12px;padding:16px 40px;font-size:32px;font-weight:700;letter-spacing:0.3em;color:#4338ca;font-family:'Courier New',monospace;text-align:center;">
        {code}
      </td></tr>
    </table>
  </td></tr>
</table>"""


def verification_email_html(code: str, lang: str = "ru") -> str:
    """HTML template for email verification code."""
    title = _t(lang, "verify_title")
    desc = _t(lang, "verify_desc")
    code_valid = _t(lang, "code_valid")
    ignore = _t(lang, "verify_ignore")
    preheader = _t(lang, "verify_preheader", code=code)

    content = f"""\
<h2 class="body-text" style="margin:0 0 8px;font-size:20px;font-weight:600;color:#111827;text-align:center;">{title}</h2>
<p class="body-text" style="margin:0 0 24px;font-size:14px;color:#6b7280;text-align:center;line-height:1.5;">
  {desc}
</p>

{_code_block(code)}

<p class="body-text" style="margin:20px 0 0;font-size:13px;color:#9ca3af;text-align:center;line-height:1.5;">
  {code_valid}<br/>
  {ignore}
</p>"""
    return _base_template(content, preheader=preheader, lang=lang)


def password_reset_email_html(code: str, lang: str = "ru") -> str:
    """HTML template for password reset code."""
    title = _t(lang, "reset_title")
    desc = _t(lang, "reset_desc")
    code_valid = _t(lang, "code_valid")
    ignore = _t(lang, "reset_ignore")
    preheader = _t(lang, "reset_preheader", code=code)

    content = f"""\
<h2 class="body-text" style="margin:0 0 8px;font-size:20px;font-weight:600;color:#111827;text-align:center;">{title}</h2>
<p class="body-text" style="margin:0 0 24px;font-size:14px;color:#6b7280;text-align:center;line-height:1.5;">
  {desc}
</p>

{_code_block(code)}

<p class="body-text" style="margin:20px 0 0;font-size:13px;color:#9ca3af;text-align:center;line-height:1.5;">
  {code_valid}<br/>
  {ignore}
</p>"""
    return _base_template(content, preheader=preheader, lang=lang)
