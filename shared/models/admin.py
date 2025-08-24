import datetime
import uuid

from sqlalchemy import (
    DateTime,
    PrimaryKeyConstraint,
    Text,
    UniqueConstraint,
    Uuid,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Admin(Base):
    __tablename__ = "admin"
    __table_args__ = (
        PrimaryKeyConstraint("admin_id", name="admin_pkey"),
        UniqueConstraint("email", name="admin_email_unique"),
        {"schema": "expo"},
    )

    admin_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    admin_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    pwd: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(True), nullable=False, server_default=text("now()")
    )
