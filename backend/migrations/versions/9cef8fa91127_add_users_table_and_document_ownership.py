"""add users table and document ownership

Revision ID: 9cef8fa91127
Revises: f3bec4b1c12f
Create Date: 2026-09-10 17:34:08.172335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9cef8fa91127'
down_revision: Union[str, Sequence[str], None] = 'f3bec4b1c12f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('role', sa.Enum('ADMIN', 'USER', name='user_role'), nullable=False),
    sa.Column('password_hash', sa.String(length=255), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.add_column('documents', sa.Column('user_id', sa.UUID(), nullable=True))
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    # Named explicitly so downgrade() can drop it - autogenerate emits
    # None here, which fails at runtime.
    op.create_foreign_key(
        'fk_documents_user_id_users',
        'documents',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )

    # user_id is deliberately left nullable. Documents ingested before auth
    # existed have no owner; the first account to register adopts them (see
    # AuthService/signup). Making it NOT NULL here would fail on any
    # database with existing rows.


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'fk_documents_user_id_users',
        'documents',
        type_='foreignkey',
    )
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_column('documents', 'user_id')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # Postgres keeps an ENUM type after its table is dropped, so a
    # subsequent upgrade would fail with "type user_role already exists"
    # unless it is dropped explicitly here.
    sa.Enum(name='user_role').drop(op.get_bind(), checkfirst=True)
