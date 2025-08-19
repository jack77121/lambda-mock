from typing import TYPE_CHECKING, Optional
import datetime
import uuid

from sqlalchemy import DateTime, ForeignKeyConstraint, PrimaryKeyConstraint, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .salesperson import Salesperson
    from .users import Users


class EvaluateVarsAndResults(Base):
    __tablename__ = 'evaluate_vars_and_results'
    __table_args__ = (
        ForeignKeyConstraint(['salesperson_id'], ['expo.salesperson.salesperson_id'], name='evaluate_vars_and_results_salesperson_id_salesperson_salesperso'),
        ForeignKeyConstraint(['user_id'], ['expo.users.user_id'], name='evaluate_vars_and_results_user_id_users_user_id_fk'),
        PrimaryKeyConstraint('evaluate_var_result_id', name='evaluate_vars_and_results_pkey'),
        {'schema': 'expo'}
    )

    evaluate_var_result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    result: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    salesperson_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    file_id: Mapped[Optional[str]] = mapped_column(Text)
    version: Mapped[Optional[str]] = mapped_column(Text, server_default=text("'0.0.1'::text"))

    salesperson: Mapped['Salesperson'] = relationship('Salesperson', back_populates='evaluate_vars_and_results')
    user: Mapped['Users'] = relationship('Users', back_populates='evaluate_vars_and_results')