"""Rename branded metadata column on zip_export_options to include_retinue_metadata

Part of the Deviant/AgentGo -> Retinue rebrand.

The historical column name is ambiguous: 7094a0d12afb's downgrade recreates it as
``include_agentgo_metadata``, while the ORM model carried ``include_Deviant_metadata``.
Depending on when a given database was provisioned it may have either name, so this
migration inspects the live schema and renames whichever variant is present.

Revision ID: 011_rename_brand_metadata
Revises: 010_multi_agent_chat
"""
from alembic import op
import sqlalchemy as sa


revision = '011_rename_brand_metadata'
down_revision = '010_multi_agent_chat'
branch_labels = None
depends_on = None

TABLE = 'zip_export_options'
NEW_NAME = 'include_retinue_metadata'
LEGACY_NAMES = ('include_Deviant_metadata', 'include_agentgo_metadata')


def _existing_columns() -> set:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if TABLE not in inspector.get_table_names():
        return set()
    return {col['name'] for col in inspector.get_columns(TABLE)}


def upgrade() -> None:
    columns = _existing_columns()
    if not columns or NEW_NAME in columns:
        return
    for legacy in LEGACY_NAMES:
        if legacy in columns:
            op.alter_column(TABLE, legacy, new_column_name=NEW_NAME)
            return


def downgrade() -> None:
    columns = _existing_columns()
    if NEW_NAME not in columns:
        return
    op.alter_column(TABLE, NEW_NAME, new_column_name=LEGACY_NAMES[0])
