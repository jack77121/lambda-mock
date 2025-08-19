from typing import Optional
import datetime
import uuid

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, REAL, SmallInteger, Text, UniqueConstraint, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Admin(Base):
    __tablename__ = 'admin'
    __table_args__ = (
        PrimaryKeyConstraint('admin_id', name='admin_pkey'),
        UniqueConstraint('email', name='admin_email_unique'),
        {'schema': 'expo'}
    )

    admin_id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, server_default=text('gen_random_uuid()'))
    admin_name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    pwd: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))


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
