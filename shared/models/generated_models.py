import uuid
from typing import Optional

from sqlalchemy import Enum, PrimaryKeyConstraint, SmallInteger, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from shared.models.base import Base


class EvaluateTasks(Base):
    __tablename__ = "evaluate_tasks"
    __table_args__ = (
        PrimaryKeyConstraint("task_id", name="evaluate_tasks_pkey"),
        {"schema": "expo"},
    )

    task_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, server_default=text("gen_random_uuid()")
    )
    config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    unit: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    df_ami: Mapped[dict] = mapped_column(JSONB, nullable=False)
    mode: Mapped[str] = mapped_column(Text, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    mode_key: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum("INIT", "SUCCESS", "FAILED", name="eval_task_status"),
        nullable=False,
        server_default=text("'INIT'::eval_task_status"),
    )
    evaluate_var_result_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    df_program: Mapped[Optional[str]] = mapped_column(Text)
    sp_program: Mapped[Optional[str]] = mapped_column(Text)
    lc_program: Mapped[Optional[str]] = mapped_column(Text)
    error_msg: Mapped[Optional[str]] = mapped_column(Text)
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
