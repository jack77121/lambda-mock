from typing import TYPE_CHECKING, Optional, list
import datetime
import uuid

from sqlalchemy import Boolean, DateTime, PrimaryKeyConstraint, Text, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .calc_vars import CalcVars
    from .computex_calc_vars_and_results import ComputexCalcVarsAndResults
    from .evaluate_vars_and_results import EvaluateVarsAndResults


class Users(Base):
    __tablename__ = 'users'
    __table_args__ = (
        PrimaryKeyConstraint('user_id', name='users_pkey'),
        {'schema': 'expo'}
    )

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    username: Mapped[Optional[str]] = mapped_column(Text)
    email: Mapped[Optional[str]] = mapped_column(Text)
    company_name: Mapped[Optional[str]] = mapped_column(Text)
    sent_report: Mapped[Optional[bool]] = mapped_column(Boolean, server_default=text('false'))

    calc_vars: Mapped[list['CalcVars']] = relationship('CalcVars', back_populates='user')
    computex_calc_vars_and_results: Mapped[list['ComputexCalcVarsAndResults']] = relationship('ComputexCalcVarsAndResults', back_populates='user')
    evaluate_vars_and_results: Mapped[list['EvaluateVarsAndResults']] = relationship('EvaluateVarsAndResults', back_populates='user')