from datetime import date, datetime
from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, func, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Standard(Base):
    __tablename__ = "standards"
    __table_args__ = (CheckConstraint("(is_mock = false OR status = 'unverified') AND (standard_code NOT LIKE 'IS-DEMO-%' OR is_mock = true)", name="ck_standards_mock_safety"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    standard_code: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    title: Mapped[str] = mapped_column(Text)
    scope: Mapped[str] = mapped_column(Text, default="", server_default="")
    abstract: Mapped[str] = mapped_column(Text, default="", server_default="")
    status: Mapped[str] = mapped_column(String(40), default="unverified", server_default="unverified")
    revision: Mapped[str | None] = mapped_column(Text)
    publication_date: Mapped[date | None] = mapped_column(Date)
    withdrawn_date: Mapped[date | None] = mapped_column(Date)
    superseded_by: Mapped[str | None] = mapped_column(String(120))
    source_url: Mapped[str | None] = mapped_column(Text)
    is_mock: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    keywords: Mapped[list["StandardKeyword"]] = relationship(cascade="all, delete-orphan", order_by="StandardKeyword.keyword")


class StandardKeyword(Base):
    __tablename__ = "standard_keywords"
    standard_id: Mapped[int] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), primary_key=True)
    keyword: Mapped[str] = mapped_column(String(200), primary_key=True)


class StandardRelationship(Base):
    __tablename__ = "standard_relationships"
    __table_args__ = (UniqueConstraint("source_standard_id", "target_standard_id", "relationship_type", name="uq_standard_relationship"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    source_standard_id: Mapped[int] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), index=True)
    target_standard_id: Mapped[int] = mapped_column(ForeignKey("standards.id", ondelete="CASCADE"), index=True)
    relationship_type: Mapped[str] = mapped_column(String(80))
