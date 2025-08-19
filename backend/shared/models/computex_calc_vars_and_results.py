from typing import TYPE_CHECKING, Optional
import datetime
import uuid

from sqlalchemy import DateTime, ForeignKeyConstraint, PrimaryKeyConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import Users


class ComputexCalcVarsAndResults(Base):
    __tablename__ = 'computex_calc_vars_and_results'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['expo.users.user_id'], name='computex_calc_vars_and_results_user_id_users_user_id_fk'),
        PrimaryKeyConstraint('calc_var_result_id', name='computex_calc_vars_and_results_pkey'),
        {'schema': 'expo'}
    )

    calc_var_result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    config: Mapped[Optional[dict]] = mapped_column(JSONB)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)

    user: Mapped[Optional['Users']] = relationship('Users', back_populates='computex_calc_vars_and_results')