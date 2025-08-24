from typing import TYPE_CHECKING, Optional, list
import uuid

from sqlalchemy import Integer, PrimaryKeyConstraint, Text, UniqueConstraint, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .salesperson import Salesperson


class Customer(Base):
    __tablename__ = 'customer'
    __table_args__ = (
        PrimaryKeyConstraint('customer_id', name='customer_pkey'),
        UniqueConstraint('customer_admin_email', name='customer_customer_admin_email_unique'),
        {'schema': 'expo'}
    )

    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    customer_name: Mapped[str] = mapped_column(Text, nullable=False)
    logo: Mapped[str] = mapped_column(Text, nullable=False)
    customer_admin_name: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'管理員'::text"))
    customer_admin_pwd: Mapped[str] = mapped_column(Text, nullable=False)
    customer_admin_email: Mapped[str] = mapped_column(Text, nullable=False)
    sales_head_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('5'))
    plan: Mapped[Optional[str]] = mapped_column(Text)
    contact_admin_phone: Mapped[Optional[str]] = mapped_column(Text)

    salesperson: Mapped[list['Salesperson']] = relationship('Salesperson', back_populates='under_customer')