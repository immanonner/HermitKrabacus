"""empty message

Revision ID: beab5bf292c8
Revises: bf3af2d67e85
Create Date: 2022-06-30 22:18:08.340484

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'beab5bf292c8'
down_revision = 'bf3af2d67e85'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('structureMarkets', sa.Column('esi_expiry', sa.String(length=200), nullable=True))
    op.drop_column('structureMarkets', 'expiry')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('structureMarkets', sa.Column('expiry', sa.DATETIME(), nullable=True))
    op.drop_column('structureMarkets', 'esi_expiry')
    # ### end Alembic commands ###