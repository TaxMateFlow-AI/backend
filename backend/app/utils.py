import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import emails  # type: ignore
import jwt
import requests
from dotenv import load_dotenv
from jinja2 import Template
from jwt.exceptions import InvalidTokenError

from app.core import security
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv();

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
FROM_EMAIL_ADDRESS = os.getenv("FROM_EMAIL_ADDRESS", "")

@dataclass
class EmailData:
    html_content: str
    subject: str


def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    template_str = (
        Path(__file__).parent / "email-templates" / "build" / template_name
    ).read_text(encoding="utf-8")
    html_content = Template(template_str).render(context)
    return html_content


def send_email(
    *,
    email_to: str,
    subject: str = "",
    html_content: str = "",
) -> None:
    MAILGUN_API_URL = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"

    try:
        resp = requests.post(MAILGUN_API_URL, auth=("api", MAILGUN_API_KEY), data={
            "from": FROM_EMAIL_ADDRESS,
            "to": email_to,
            "subject": subject,
            "html": html_content
        })
        if resp.status_code == 200:
            logger.info(f"send email result: {resp.json()}")
        else:
            logger.error(f"send email result: {resp.json()}")
    except Exception as e:
        logger.error(f"send email result: {e}")



def generate_test_email(email_to: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Test email"
    html_content = render_email_template(
        template_name="test_email.html",
        context={"username": "James", "link": "google.com"},
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_reset_password_email(email_to: str, email: str, token: str) -> EmailData:
    project_name = settings.PROJECT_NAME
    subject = f"{project_name} - Password recovery for user {email}"
    link = f"{settings.FRONTEND_HOST}/reset-password?token={token}"
    html_content = render_email_template(
        template_name="reset_password.html",
        context={
            "project_name": settings.PROJECT_NAME,
            "username": email,
            "email": email_to,
            "valid_hours": settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS,
            "link": link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_new_account_email(
    username: str, link: str
) -> EmailData:
    verification_link = link
    subject = f"TaxMate - New account for user {username}"
    html_content = render_email_template(
        template_name="template_signup.html",
        context={
            "name": username,
            "link": verification_link,
        },
    )
    return EmailData(html_content=html_content, subject=subject)

def generate_login_email(code: str) -> EmailData:
    verification_code = code
    subject = "Verification - Code for TaxMate"
    html_content = render_email_template(
        template_name="template_signin.html",
        context={
            "verification_code": verification_code
        },
    )
    return EmailData(html_content=html_content, subject=subject)


def generate_password_reset_token(email: str) -> str:
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    exp = expires.timestamp()
    encoded_jwt = jwt.encode(
        {"exp": exp, "nbf": now, "sub": email},
        settings.SECRET_KEY,
        algorithm=security.ALGORITHM,
    )
    return encoded_jwt


def verify_password_reset_token(token: str) -> str | None:
    try:
        decoded_token = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        return str(decoded_token["sub"])
    except InvalidTokenError:
        return None