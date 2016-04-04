"""add_test_owner

Revision ID: 230e225657d0
Revises: 290a71847cd7
Create Date: 2016-02-18 00:14:58.856828

"""

# revision identifiers, used by Alembic.
revision = '230e225657d0'
down_revision = '290a71847cd7'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text
from sqlalchemy.dialects import postgresql

def upgrade():
    '''The autovacuum process on postgres permanently locks the 'test' table
    so it can't be altered. We need to kill the autovacuumer, then execute our
    ALTER as part of the same SQL statement before the vacuumer gets restarted
    by postgres.'''
    # This commented code line below is the code autogenerated by alembic. It
    # represents the intention of what we're trying to do, but it's
    # insufficient due to the autovacuumer lock.
    # op.add_column('test', sa.Column('owner', sa.Text(), nullable=True))

    # Use the following code instead.
    # NOTE: The 'procpid' column is renamed to 'pid' in trusty-era Postgresql.
    #       If we migrate to trusty and run into problems here, that's probably
    #       why.
    conn = op.get_bind()
    conn.execute(text('''SELECT pg_terminate_backend(procpid)
                         FROM pg_stat_activity
                         WHERE current_query = 'autovacuum: VACUUM public.test (to prevent wraparound)';
                         BEGIN;
                         ALTER TABLE test ADD COLUMN owner TEXT;
                         UPDATE alembic_version SET version_num=:revision;
                         COMMIT;'''),
                         revision=revision)


def downgrade():
    '''The autovacuum process on postgres permanently locks the 'test' table
    so it can't be altered. We need to kill the autovacuumer, then execute our
    ALTER as part of the same SQL statement before the vacuumer gets restarted
    by postgres.'''
    # This commented code line below is the code autogenerated by alembic. It
    # represents the intention of what we're trying to do, but it's
    # insufficient due to the autovacuumer lock.
    # op.drop_column('test', 'owner')

    # Use the following code instead.
    # NOTE: The 'procpid' column is renamed to 'pid' in trusty-era Postgresql.
    #       If we migrate to trusty and run into problems here, that's probably
    #       why.
    conn.execute(text('''SELECT pg_terminate_backend(procpid)
                         FROM pg_stat_activity
                         WHERE current_query = 'autovacuum: VACUUM public.test (to prevent wraparound)';
                         BEGIN;
                         ALTER TABLE test DROP COLUMN owner;
                         UPDATE alembic_version SET version_num=:down_revision;
                         COMMIT;'''),
                         down_revision=down_revision)