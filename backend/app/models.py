import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class VotingGuideSignup(Base):
    __tablename__ = "voting_guide_signups"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    voting_method: Mapped[str] = mapped_column(String(20))  # 'consulate' or 'mail'
    language_pref: Mapped[str] = mapped_column(String(2), default="hu")
    signup_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)


class VotingGuideContact(Base):
    __tablename__ = "voting_guide_contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    message: Mapped[str] = mapped_column(Text)
    language_pref: Mapped[str] = mapped_column(String(2), default="hu")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class VotingGuideHelpRequest(Base):
    __tablename__ = "voting_guide_help_requests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    message: Mapped[str] = mapped_column(Text)
    voting_method: Mapped[str] = mapped_column(String(20))
    language_pref: Mapped[str] = mapped_column(String(2), default="hu")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class VotingGuideCarpool(Base):
    __tablename__ = "voting_guide_carpools"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    carpool_type: Mapped[str] = mapped_column(String(10))  # 'offer' or 'seek'
    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    starting_location: Mapped[str] = mapped_column(String(500))
    seats: Mapped[int | None] = mapped_column(nullable=True)  # required for offers
    voting_method: Mapped[str] = mapped_column(String(20))
    language_pref: Mapped[str] = mapped_column(String(2), default="hu")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
