"""Add ondelete CASCADE and RESTRICT to company_talent_values FKs

Revision ID: fad7f679df3e
Revises: 9df302dfe854
Create Date: 2026-02-08 17:12:24.278679

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'fad7f679df3e'
down_revision: Union[str, None] = '9df302dfe854'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint('company_talent_values_company_id_fkey', 'company_talent_values', type_='foreignkey')
    op.drop_constraint('company_talent_values_job_category_id_fkey', 'company_talent_values', type_='foreignkey')
    op.create_foreign_key('company_talent_values_company_id_fkey', 'company_talent_values', 'companies', ['company_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('company_talent_values_job_category_id_fkey', 'company_talent_values', 'job_categories', ['job_category_id'], ['id'], ondelete='RESTRICT')


def downgrade() -> None:
    op.drop_constraint('company_talent_values_job_category_id_fkey', 'company_talent_values', type_='foreignkey')
    op.drop_constraint('company_talent_values_company_id_fkey', 'company_talent_values', type_='foreignkey')
    op.create_foreign_key('company_talent_values_company_id_fkey', 'company_talent_values', 'companies', ['company_id'], ['id'])
    op.create_foreign_key('company_talent_values_job_category_id_fkey', 'company_talent_values', 'job_categories', ['job_category_id'], ['id'])
