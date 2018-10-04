"""add language to posts

Revision ID: 5138ca0ef77a
Revises: 6891ed2fd57a
Create Date: 2018-09-03 12:07:00.025593

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5138ca0ef77a'
down_revision = '6891ed2fd57a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #op.add_column('post', sa.Column('language', sa.String(length=5), nullable=True))
    # ### end Alembic commands ###
    pass


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('post', 'language')
    # ### end Alembic commands ###