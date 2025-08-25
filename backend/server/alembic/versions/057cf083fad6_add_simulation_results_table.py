"""Add simulation_results table

Revision ID: 057cf083fad6
Revises: 
Create Date: 2025-08-24 21:29:09.318537

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '057cf083fad6'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create simulation_results table
    op.create_table(
        'simulation_results',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('evaluate_var_result_id', sa.String(), nullable=False, index=True),
        sa.Column('simulation_id', sa.String(), nullable=False, unique=True),
        sa.Column('mode_key', sa.String(), nullable=False),
        sa.Column('unit', sa.Integer(), nullable=False),
        sa.Column('simulation_params', sa.JSON(), nullable=False),
        sa.Column('result_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_time', sa.Float(), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_simulation_results_evaluate_var_result_id', 'simulation_results', ['evaluate_var_result_id'])
    op.create_index('ix_simulation_results_status', 'simulation_results', ['status'])
    op.create_index('ix_simulation_results_created_at', 'simulation_results', ['created_at'])


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes first
    op.drop_index('ix_simulation_results_created_at')
    op.drop_index('ix_simulation_results_status')
    op.drop_index('ix_simulation_results_evaluate_var_result_id')
    
    # Drop table
    op.drop_table('simulation_results')
