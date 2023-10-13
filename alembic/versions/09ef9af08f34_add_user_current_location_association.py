"""Add user_current_location_association

Revision ID: 09ef9af08f34
Revises: 71d0fd4523c7
Create Date: 2023-10-10 11:56:13.177199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09ef9af08f34'
down_revision: Union[str, None] = '71d0fd4523c7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_current_location_association',
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('location_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['location_id'], ['location.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE')
    )
    op.drop_index('ix_location_compound_code', table_name='location')
    op.drop_index('ix_location_global_code', table_name='location')
    op.create_index('idx_latitude_longitude', 'location', ['latitude', 'longitude'], unique=False)
    op.create_index(op.f('ix_location_latitude'), 'location', ['latitude'], unique=False)
    op.create_index(op.f('ix_location_longitude'), 'location', ['longitude'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_location_longitude'), table_name='location')
    op.drop_index(op.f('ix_location_latitude'), table_name='location')
    op.drop_index('idx_latitude_longitude', table_name='location')
    op.create_index('ix_location_global_code', 'location', ['global_code'], unique=False)
    op.create_index('ix_location_compound_code', 'location', ['compound_code'], unique=False)
    op.drop_table('user_current_location_association')
    # ### end Alembic commands ###