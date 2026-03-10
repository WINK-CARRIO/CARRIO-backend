"""merge heads

Revision ID: 94831ceee69f
Revises: ab9d49d177c5, fad7f679df3e
Create Date: 2026-02-13 19:40:03.898675

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '94831ceee69f'
down_revision: Union[str, None] = ('ab9d49d177c5', 'fad7f679df3e')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
