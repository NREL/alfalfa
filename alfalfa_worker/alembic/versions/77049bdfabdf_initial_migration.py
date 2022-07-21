"""initial migration

Revision ID: 77049bdfabdf
Revises:
Create Date: 2022-07-21 09:35:26.112722

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '77049bdfabdf'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('site',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('haystack', postgresql.JSON(astext_type=sa.Text()), nullable=True),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('model',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('file', sa.String(), nullable=True),
                    sa.Column('site_id', sa.Integer(), nullable=True),
                    sa.ForeignKeyConstraint(['site_id'], ['site.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('run',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('site_id', sa.Integer(), nullable=True),
                    sa.Column('model_id', sa.Integer(), nullable=True),
                    sa.Column('run_dir', sa.String(), nullable=True),
                    sa.Column('sim_type', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['model_id'], ['model.id'], ),
                    sa.ForeignKeyConstraint(['site_id'], ['site.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    op.create_table('point',
                    sa.Column('id', sa.String(), nullable=False),
                    sa.Column('created_at', sa.DateTime(), nullable=False),
                    sa.Column('updated_at', sa.DateTime(), nullable=True),
                    sa.Column('key', sa.String(), nullable=True),
                    sa.Column('name', sa.String(), nullable=True),
                    sa.Column('run_id', sa.Integer(), nullable=True),
                    sa.Column('value', sa.String(), nullable=True),
                    sa.ForeignKeyConstraint(['run_id'], ['run.id'], ),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('point')
    op.drop_table('run')
    op.drop_table('model')
    op.drop_table('site')
    # ### end Alembic commands ###