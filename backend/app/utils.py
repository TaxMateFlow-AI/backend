import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
from pathlib import Path
from typing import Any
import mailchimp_marketing as MailChimpMarketing
from aiohttp import ClientError
import boto3
from botocore.exceptions import BotoCoreError
from google.auth.environment_vars import AWS_REGION
from mailchimp_marketing.api_client import ApiClientError

mailchimp = MailChimpMarketing.Client()
mailchimp.set_config({
    "api_key": "f144f080eb70fda4598fa4f3e19b7fde-us8",
    "server": "us8"  # e.g., 'us1', 'us2'
})

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

FROM_EMAIL_ADDRESS = os.getenv("FROM_EMAIL_ADDRESS", "")
AWS_REGION = os.getenv("AWS_REGION", "")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")

ses_client = boto3.client(
    "ses",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

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
    email_to: str,
    subject: str = "",
    html_content: str = "",
):
    try:
        response = ses_client.send_email(
            Source=FROM_EMAIL_ADDRESS,  # Replace with your verified address
            Destination={"ToAddresses": [email_to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Html": {"Data": html_content, "Charset": "UTF-8"},
                },
            },
        )
        logging.info(f"Email sent successfully! Message ID: {response['MessageId']}")
        return {"message": "Email sent successfully!", "message_id": response["MessageId"]}
    except ClientError as e:
        logging.error(f"AWS SES ClientError: {e.response['Error']['Message']}")
        raise HTTPException(status_code=500, detail=f"Error sending email: {e.response['Error']['Message']}")
    except BotoCoreError as e:
        logging.error(f"BotoCoreError: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


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