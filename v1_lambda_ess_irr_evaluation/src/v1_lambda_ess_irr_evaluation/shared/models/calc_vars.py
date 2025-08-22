from typing import TYPE_CHECKING, Optional, list
import datetime
import uuid

from sqlalchemy import ARRAY, DateTime, Enum, ForeignKeyConstraint, PrimaryKeyConstraint, REAL, SmallInteger, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .users import Users
    from .calc_results import CalcResults


class CalcVars(Base):
    __tablename__ = 'calc_vars'
    __table_args__ = (
        ForeignKeyConstraint(['user_id'], ['expo.users.user_id'], name='calc_vars_user_id_users_user_id_fk'),
        PrimaryKeyConstraint('calc_var_id', name='calc_vars_pkey'),
        {'schema': 'expo'}
    )

    calc_var_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    trial_calc_type: Mapped[str] = mapped_column(Enum('single_basic', 'single_ancillary', 'aggregate_ancillary', 'negative_irr', name='trial_calc_type'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    capacity: Mapped[Optional[float]] = mapped_column(REAL)
    price_type: Mapped[Optional[str]] = mapped_column(Text)
    industry: Mapped[Optional[str]] = mapped_column(Text)
    chart_ids: Mapped[Optional[str]] = mapped_column(Text)
    work_day: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()), server_default=text('ARRAY[]::text[]'))
    work_hour: Mapped[Optional[list[int]]] = mapped_column(ARRAY(SmallInteger()), server_default=text('ARRAY[]::smallint[]'))
    work_threshold: Mapped[Optional[float]] = mapped_column(REAL)
    rest_threshold: Mapped[Optional[float]] = mapped_column(REAL)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    user: Mapped[Optional['Users']] = relationship('Users', back_populates='calc_vars')
    calc_results: Mapped[list['CalcResults']] = relationship('CalcResults', back_populates='calc_var')