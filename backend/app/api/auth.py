import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    EmailRequest,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    SignupResponse,
    UserRecord,
)
from app.services.auth import (
    create_access_token,
    create_email_token,
    decode_email_token,
    hash_password,
    verify_password,
)
from app.services.mailer import send_email

router = APIRouter(prefix="/auth", tags=["Auth"])

user_repository = UserRepository()


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        httponly=True,          # unreadable from JavaScript, so an XSS bug
                                # cannot exfiltrate the session
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.JWT_EXPIRE_MINUTES * 60,
        path="/",
    )


async def _send_verification_email(user: User) -> None:
    token = create_email_token(str(user.id))
    link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

    await send_email(
        to=user.email,
        subject="Verify your Project Atlas email",
        body=(
            f"Hi {user.name},\n\n"
            "Confirm your email address to finish setting up your "
            "Project Atlas account:\n\n"
            f"{link}\n\n"
            f"This link expires in {settings.EMAIL_TOKEN_EXPIRE_MINUTES} "
            "minutes.\n\n"
            "If you didn't create this account, you can ignore this email."
        ),
    )


@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(
    request: SignupRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> SignupResponse:

    existing = await user_repository.get_by_email(
        session=session,
        email=request.email,
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with that email already exists.",
        )

    # The first account to register becomes the administrator and adopts
    # every document ingested before auth existed. Bootstrapping this way
    # avoids seeding a user with a fabricated password in a migration.
    is_first_user = await user_repository.count(session=session) == 0

    requires_verification = settings.REQUIRE_EMAIL_VERIFICATION

    user = await user_repository.create(
        session=session,
        name=request.name,
        email=request.email,
        password_hash=hash_password(request.password),
        role=UserRole.ADMIN if is_first_user else UserRole.USER,
        verified=not requires_verification,
    )

    if is_first_user:
        await user_repository.adopt_ownerless_documents(
            session=session,
            user_id=user.id,
        )

    await session.commit()

    if requires_verification:
        # No session cookie: an unverified account is created but cannot
        # act until the address is confirmed.
        await _send_verification_email(user)
        return SignupResponse(
            user=UserRecord.model_validate(user),
            authenticated=False,
            message=(
                "Account created. Check your email for a verification "
                "link before signing in."
            ),
        )

    _set_session_cookie(
        response,
        create_access_token(user_id=str(user.id), email=user.email),
    )

    return SignupResponse(
        user=UserRecord.model_validate(user),
        authenticated=True,
        message="Account created.",
    )


@router.post("/login")
async def login(
    request: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db),
) -> UserRecord:

    user = await user_repository.get_by_email(
        session=session,
        email=request.email,
    )

    # One message for "no such account" and "wrong password" alike -
    # distinguishing them turns the login form into an account-existence
    # oracle.
    invalid = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password.",
    )

    if user is None:
        raise invalid

    if not verify_password(request.password, user.password_hash):
        raise invalid

    # Checked only AFTER the password is confirmed. Reporting "not
    # verified" to someone who failed the password check would leak both
    # that the account exists and what state it is in.
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Email not verified. Check your inbox for the "
                "verification link."
            ),
        )

    _set_session_cookie(
        response,
        create_access_token(user_id=str(user.id), email=user.email),
    )

    return UserRecord.model_validate(user)


@router.post("/logout")
async def logout(response: Response) -> MessageResponse:
    # delete_cookie must match the attributes the cookie was set with, or
    # the browser keeps the original.
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        path="/",
    )
    return MessageResponse(message="Logged out.")


@router.get("/me")
async def me(user: User = Depends(get_current_user)) -> UserRecord:
    return UserRecord.model_validate(user)


@router.get("/verify-email")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:

    user_id = decode_email_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )

    try:
        parsed_id = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )

    user = await user_repository.get(session=session, user_id=parsed_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This verification link is invalid or has expired.",
        )

    # Verifying an already-verified account succeeds rather than erroring.
    # Mail clients pre-fetch links and people click them twice; the second
    # click should not look like a failure.
    if not user.verified:
        await user_repository.mark_verified(session=session, user_id=user.id)
        await session.commit()

    return MessageResponse(
        message="Email verified. You can now sign in."
    )


@router.post("/resend-verification")
async def resend_verification(
    request: EmailRequest,
    session: AsyncSession = Depends(get_db),
) -> MessageResponse:

    user = await user_repository.get_by_email(
        session=session,
        email=request.email,
    )

    # Always the same reply, whether or not the account exists and whether
    # or not it is already verified. Anything else turns this endpoint into
    # the account-existence oracle that /login carefully avoids being.
    reply = MessageResponse(
        message=(
            "If that address needs verifying, a new link is on its way."
        )
    )

    if user is None or user.verified:
        return reply

    await _send_verification_email(user)

    return reply
