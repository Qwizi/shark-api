"""empty message

Revision ID: f0613d78cfa8
Revises: f39425298097
Create Date: 2022-12-17 19:41:33.323508

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f0613d78cfa8'
down_revision = 'f39425298097'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('scopes', sa.Column('protected', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('scopes', 'protected')
    # ### end Alembic commands ###
