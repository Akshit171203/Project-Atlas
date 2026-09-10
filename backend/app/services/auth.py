from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings

# bcrypt truncates silently at 72 bytes. Rejecting longer passwords is
# better than accepting one and only validating its first 72 bytes.
MAX_PASSWORD_BYTES = 72


def hash_password(password: str) -> str:
    # cost factor 10 matches the genSalt(10) used in the reference
    # implementation this was ported from.
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    # An account with no password hash is OAuth-only (or not yet set up).
    # Return False rather than treating "no password" as "any password".
    if not password_hash:
        return False
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        # Malformed/legacy hash in the column — treat as a failed login
        # rather than a 500.
        return False


def create_access_token(user_id: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


EMAIL_VERIFICATION = "emailVerification"


def create_email_token(user_id: str, token_type: str = EMAIL_VERIFICATION) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        # The type claim stops a token minted for one purpose being
        # replayed for another (e.g. a verification link used as a
        # password-reset token) even though both are signed with the same
        # email secret.
        "type": token_type,
        "iat": now,
        "exp": now + timedelta(minutes=settings.EMAIL_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(
        payload,
        settings.EMAIL_TOKEN_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_email_token(
    token: str,
    expected_type: str = EMAIL_VERIFICATION,
) -> str | None:
    """Return the user id from a valid email token, or None."""
    try:
        payload = jwt.decode(
            token,
            settings.EMAIL_TOKEN_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None

    if payload.get("type") != expected_type:
        return None

    return payload.get("sub")


def decode_access_token(token: str) -> dict | None:
    try:
        # algorithms is an allow-list, not a hint: without it a token could
        # declare alg=none and be accepted unsigned.
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.PyJWTError:
        return None
