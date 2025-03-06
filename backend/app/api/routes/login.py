from datetime import timedelta
from typing import Annotated, Any
import random
import string
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordRequestForm

from app import crud
from app.api.deps import CurrentUser, SessionDep, get_current_active_superuser
from app.core import security
from app.core.config import settings
from app.core.security import get_password_hash
from app.models import Message, NewPassword, Token, UserPublic, VerifyCodeRequest
from app.utils import (
    generate_password_reset_token,
    generate_reset_password_email,
    send_email,
    verify_password_reset_token, generate_login_email,
)

router = APIRouter(tags=["login"])

# In-memory storage for verification codes (use a database in production)
verification_codes = {}

def generate_verification_code(length: int = 6) -> str:
    """
    Generate a random numeric verification code.
    """
    return ''.join(random.choices(string.digits, k=length))


@router.post("/login/access-token")
def login_access_token(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
    )

@router.post("/login/verify-code")
def verify_code(
    request: VerifyCodeRequest,  # Use the Pydantic model to parse the request body
    session: SessionDep,
) -> Token:
    """
    Verify the user's email and the provided verification code.
    """
    email = request.email
    verification_code = request.verification_code

    # Check if the email exists in the verification codes
    if email not in verification_codes:
        raise HTTPException(status_code=400, detail="Verification code not found.")

    # Retrieve the verification code and expiration time
    code_data = verification_codes[email]
    stored_code = code_data["code"]
    expires_at = code_data["expires_at"]

    # Check if the verification code is expired
    if datetime.utcnow() > expires_at:
        # Remove the expired code
        del verification_codes[email]
        raise HTTPException(status_code=400, detail="Verification code has expired.")

    # Check if the provided verification code matches
    if stored_code != verification_code:
        raise HTTPException(status_code=401, detail="Invalid verification code.")

    # Remove the verification code after it's been successfully used
    del verification_codes[email]

    # Fetch the user from the database
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user.")

    # Generate an access token for the user
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return Token(
        access_token=security.create_access_token(
            user.id, expires_delta=access_token_expires
        ), email=user.email
    )

@router.post("/login/send-verification-code")
def send_verification_code(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Message:
    """
    Send a verification code to the user's email after validating email and password.
    """
    # Authenticate the user using email and password
    user = crud.authenticate(
        session=session, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # Generate a 6-digit verification code
    verification_code = generate_verification_code()

    # Calculate expiration time (current time + 60 seconds)
    expiration_time = datetime.utcnow() + timedelta(seconds=60)

    # Save the verification code and expiration time in memory
    verification_codes[user.email] = {"code": verification_code, "expires_at": expiration_time}

    print("------>", f"{verification_code}")

    # Send the verification code via email
    email_data = generate_login_email(code=verification_code)

    send_email(
        email_to=user.email,
        subject="Your Verification Code",
        html_content=email_data.html_content,
    )

    return Message(message="Verification code sent to your email.")

@router.post("/login/test-token", response_model=UserPublic)
def test_token(current_user: CurrentUser) -> Any:
    """
    Test access token
    """
    return current_user


@router.post("/password-recovery/{email}")
def recover_password(email: str, session: SessionDep) -> Message:
    """
    Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )
    send_email(
        email_to=user.email,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Password recovery email sent")


@router.post("/reset-password/")
def reset_password(session: SessionDep, body: NewPassword) -> Message:
    """
    Reset password
    """
    email = verify_password_reset_token(token=body.token)
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token")
    user = crud.get_user_by_email(session=session, email=email)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this email does not exist in the system.",
        )
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    hashed_password = get_password_hash(password=body.new_password)
    user.hashed_password = hashed_password
    session.add(user)
    session.commit()
    return Message(message="Password updated successfully")


@router.post(
    "/password-recovery-html-content/{email}",
    dependencies=[Depends(get_current_active_superuser)],
    response_class=HTMLResponse,
)
def recover_password_html_content(email: str, session: SessionDep) -> Any:
    """
    HTML Content for Password Recovery
    """
    user = crud.get_user_by_email(session=session, email=email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="The user with this username does not exist in the system.",
        )
    password_reset_token = generate_password_reset_token(email=email)
    email_data = generate_reset_password_email(
        email_to=user.email, email=email, token=password_reset_token
    )

    return HTMLResponse(
        content=email_data.html_content, headers={"subject:": email_data.subject}
    )
