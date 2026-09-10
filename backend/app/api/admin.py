from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRecord

router = APIRouter(prefix="/admin", tags=["Admin"])

user_repository = UserRepository()


@router.get("/users")
async def list_users(
    session: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> list[UserRecord]:

    users = await user_repository.list_all(session=session)

    return [UserRecord.model_validate(user) for user in users]
