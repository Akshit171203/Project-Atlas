import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.services.auth import decode_access_token

user_repository = UserRepository()


async def get_db() -> AsyncGenerator:
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the caller from the session cookie.

    The user is re-read from the database on every request rather than
    trusted from the token body. A JWT is a snapshot of who the user was
    when it was signed - if the account was deleted or its role changed
    since, only a fresh read reflects that.
    """
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
        )

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired session.",
        )

    try:
        user_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid session token.",
        )

    user = await user_repository.get(session=session, user_id=user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists.",
        )

    return user


async def require_admin(
    user: User = Depends(get_current_user),
) -> User:
    # 403, not 401: the caller proved who they are, they just aren't
    # allowed. Returning 401 here would tell a logged-in user to log in
    # again, which never fixes anything.
    if user.role is not UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return user
