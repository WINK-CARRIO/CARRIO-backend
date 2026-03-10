"""Add check constraint for scope and job_category_id consistency

Revision ID: 9df302dfe854
Revises: 09fcdb983690
Create Date: 2026-02-08 17:04:02.421318

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '9df302dfe854'
down_revision: Union[str, None] = '09fcdb983690'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_scope_job_category_consistency",
        "company_talent_values",
        "(scope = 'company' AND job_category_id IS NULL) OR "
        "(scope = 'job_category' AND job_category_id IS NOT NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_scope_job_category_consistency", "company_talent_values", type_="check")
