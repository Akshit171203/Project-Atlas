# To be implemented
from datetime import datetime, timezone

import uuid

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    filename: Mapped[str] = mapped_column(String)

    total_pages: Mapped[int] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc).replace(tzinfo=None),
    )

    # Nullable at the database level so the migration can add the column to
    # existing rows. It is backfilled to the first registered user (who is
    # seeded as ADMIN) the moment that account is created - see
    # AuthService.register. Application code always sets it on upload.
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )

    owner = relationship("User", back_populates="documents")
    
    chunks = relationship(
    "Chunk",
    back_populates="document",
    cascade="all, delete-orphan",
    )