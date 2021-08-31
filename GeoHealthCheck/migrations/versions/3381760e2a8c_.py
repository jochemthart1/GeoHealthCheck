"""empty message

Revision ID: 3381760e2a8c
Revises: f72ff1ac3967
Create Date: 2021-08-20 09:53:01.704105

"""
from alembic import op
from GeoHealthCheck.migrations import alembic_helpers


# revision identifiers, used by Alembic.
revision = '3381760e2a8c'
down_revision = 'f72ff1ac3967'
branch_labels = None
depends_on = None

    
def upgrade():
    # Only create indexes if not-existing
    print('Create indexes if not-existing...')
    alembic_helpers.create_index('ix_check_vars_probe_vars_identifier', 'check_vars', ['probe_vars_identifier'], unique=False)
    alembic_helpers.create_index('ix_probe_vars_resource_identifier', 'probe_vars', ['resource_identifier'], unique=False)
    alembic_helpers.create_index('ix_resource_owner_identifier', 'resource', ['owner_identifier'], unique=False)
    alembic_helpers.create_index('ix_resource_tags_resource_identifier', 'resource_tags', ['resource_identifier'], unique=False)
    alembic_helpers.create_index('ix_resource_tags_tag_id', 'resource_tags', ['tag_id'], unique=False)
    alembic_helpers.create_index('ix_run_resource_identifier', 'run', ['resource_identifier'], unique=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_run_resource_identifier'), table_name='run')
    op.drop_index(op.f('ix_resource_tags_tag_id'), table_name='resource_tags')
    op.drop_index(op.f('ix_resource_tags_resource_identifier'), table_name='resource_tags')
    op.drop_index(op.f('ix_resource_owner_identifier'), table_name='resource')
    op.drop_index(op.f('ix_probe_vars_resource_identifier'), table_name='probe_vars')
    op.drop_index(op.f('ix_check_vars_probe_vars_identifier'), table_name='check_vars')
    # ### end Alembic commands ###
