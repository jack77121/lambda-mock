from typing import TYPE_CHECKING, Optional, list
import datetime
import uuid

from sqlalchemy import DateTime, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .customer import Customer
    from .evaluate_vars_and_results import EvaluateVarsAndResults


class Salesperson(Base):
    __tablename__ = 'salesperson'
    __table_args__ = (
        ForeignKeyConstraint(['under_customer_id'], ['expo.customer.customer_id'], name='salesperson_under_customer_id_customer_customer_id_fk'),
        PrimaryKeyConstraint('salesperson_id', name='salesperson_pkey'),
        UniqueConstraint('email', name='salesperson_email_unique'),
        {'schema': 'expo'}
    )

    salesperson_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    salesperson_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    pwd: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    under_customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    expired_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text("'2222-02-02 02:02:02+08'::timestamp with time zone"))
    current_session_version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))
    favorite_config: Mapped[Optional[dict]] = mapped_column(JSONB)

    under_customer: Mapped['Customer'] = relationship('Customer', back_populates='salesperson')
    evaluate_vars_and_results: Mapped[list['EvaluateVarsAndResults']] = relationship('EvaluateVarsAndResults', back_populates='salesperson')