"""Enhance message status tracking

Revision ID: 006_enhance_message_status
Revises: 005_add_conversations
Create Date: 2025-11-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP


# revision identifiers, used by Alembic.
revision = '006_enhance_message_status'
down_revision = ('005_conversations', '7094a0d12afb')  # Merge both branches
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create MessageStatus enum
    message_status = sa.Enum(
        'SENT', 'RECEIVED', 'READ', 'IN_PROGRESS', 'RESOLVED', 'ESCALATED', 'CANCELLED',
        name='messagestatus',
        create_type=True
    )
    message_status.create(op.get_bind(), checkfirst=True)

    # Add new status column (defaults to SENT)
    op.add_column('messages', sa.Column('status', message_status, nullable=False, server_default='SENT'))

    # Add tracking timestamp columns
    op.add_column('messages', sa.Column('received_at', TIMESTAMP, nullable=True))
    op.add_column('messages', sa.Column('read_at', TIMESTAMP, nullable=True))
    op.add_column('messages', sa.Column('resolved_at', TIMESTAMP, nullable=True))

    # Add tracking agent ID columns
    op.add_column('messages', sa.Column('read_by_agent_id', sa.String(100), nullable=True))
    op.add_column('messages', sa.Column('resolved_by_agent_id', sa.String(100), nullable=True))

    # Add foreign key constraints
    op.create_foreign_key(
        'messages_read_by_agent_id_fkey',
        'messages', 'agents',
        ['read_by_agent_id'], ['agent_id']
    )
    op.create_foreign_key(
        'messages_resolved_by_agent_id_fkey',
        'messages', 'agents',
        ['resolved_by_agent_id'], ['agent_id']
    )

    # Add resolution note column
    op.add_column('messages', sa.Column('resolution_note', sa.Text, nullable=True))

    # Create indexes for better query performance
    op.create_index('idx_messages_status', 'messages', ['status'])
    op.create_index('idx_messages_to_agent_status', 'messages', ['to_agent_id', 'status'])

    # Migrate existing data: set read messages to READ status
    op.execute("""
        UPDATE messages
        SET status = 'READ', read_at = timestamp
        WHERE read_status = true
    """)

    # Set unread messages to RECEIVED status
    op.execute("""
        UPDATE messages
        SET status = 'RECEIVED', received_at = timestamp
        WHERE read_status = false
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_messages_to_agent_status', 'messages')
    op.drop_index('idx_messages_status', 'messages')

    # Drop foreign key constraints
    op.drop_constraint('messages_resolved_by_agent_id_fkey', 'messages', type_='foreignkey')
    op.drop_constraint('messages_read_by_agent_id_fkey', 'messages', type_='foreignkey')

    # Drop columns
    op.drop_column('messages', 'resolution_note')
    op.drop_column('messages', 'resolved_by_agent_id')
    op.drop_column('messages', 'read_by_agent_id')
    op.drop_column('messages', 'resolved_at')
    op.drop_column('messages', 'read_at')
    op.drop_column('messages', 'received_at')
    op.drop_column('messages', 'status')

    # Drop enum type
    sa.Enum(name='messagestatus').drop(op.get_bind(), checkfirst=True)
