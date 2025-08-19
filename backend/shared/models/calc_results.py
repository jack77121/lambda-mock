from typing import TYPE_CHECKING, Optional
import uuid

from sqlalchemy import ForeignKeyConstraint, PrimaryKeyConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .calc_vars import CalcVars


class CalcResults(Base):
    __tablename__ = 'calc_results'
    __table_args__ = (
        ForeignKeyConstraint(['calc_var_id'], ['expo.calc_vars.calc_var_id'], name='calc_results_calc_var_id_calc_vars_calc_var_id_fk'),
        PrimaryKeyConstraint('calc_result_id', name='calc_results_pkey'),
        {'schema': 'expo'}
    )

    calc_result_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    calc_var_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    calc_var: Mapped[Optional['CalcVars']] = relationship('CalcVars', back_populates='calc_results')