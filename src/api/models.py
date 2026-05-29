from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import (
    String, Boolean, Float, ForeignKey, Table, Column, Text, DateTime,
    UniqueConstraint, CheckConstraint, Index, Enum as SAEnum
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()

# ── Association table for event participants ─────────────
event_participants = Table(
    "event_participants",
    db.metadata,
    Column("event_id", ForeignKey("event.id"), primary_key=True),
    Column("user_id",  ForeignKey("user.id"),  primary_key=True),
)


# ── USER ─────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = "user"

    id:        Mapped[int]  = mapped_column(primary_key=True)
    email:     Mapped[str]  = mapped_column(String(120), unique=True, nullable=False)
    password:  Mapped[str]  = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean(), nullable=False)

    username:            Mapped[str] = mapped_column(String(50),  unique=True, nullable=True)
    first_name:          Mapped[str] = mapped_column(String(50),  nullable=True)
    last_name:           Mapped[str] = mapped_column(String(50),  nullable=True)
    city:                Mapped[str] = mapped_column(String(100), nullable=True)
    bio:                 Mapped[str] = mapped_column(Text,        nullable=True)
    profile_picture_url: Mapped[str] = mapped_column(String(500), nullable=True)
    birthdate:           Mapped[str] = mapped_column(String(20),  nullable=True)
    phone:               Mapped[str] = mapped_column(String(30),  nullable=True)
    created_at:          Mapped[datetime] = mapped_column(DateTime, nullable=True, default=datetime.utcnow)

    def serialize(self):
        return {
            "id":                  self.id,
            "email":               self.email,
            "username":            self.username,
            "first_name":          self.first_name,
            "last_name":           self.last_name,
            "city":                self.city,
            "bio":                 self.bio,
            "profile_picture_url": self.profile_picture_url,
            "birthdate":           self.birthdate,
            "phone":               self.phone,
            "created_at":          self.created_at.isoformat() if self.created_at else None,
        }

    def public_brief(self):
        """Versión reducida para chat (sin info sensible)."""
        return {
            "id":                  self.id,
            "username":            self.username,
            "email":               self.email,
            "first_name":          self.first_name,
            "last_name":           self.last_name,
            "profile_picture_url": self.profile_picture_url,
        }


# ── EVENT ─────────────────────────────────────────────────
class Event(db.Model):
    __tablename__ = "event"

    id:         Mapped[int]   = mapped_column(primary_key=True)
    date:       Mapped[str]   = mapped_column(String(50),  nullable=False)
    time:       Mapped[str]   = mapped_column(String(50),  nullable=False)
    location:   Mapped[str]   = mapped_column(String(255), nullable=False)
    latitude:   Mapped[float] = mapped_column(Float,       nullable=True)
    longitude:  Mapped[float] = mapped_column(Float,       nullable=True)
    details:    Mapped[str]   = mapped_column(Text,        nullable=True)
    image:      Mapped[str]   = mapped_column(String(500), nullable=True)
    creator_id: Mapped[int]   = mapped_column(ForeignKey("user.id"), nullable=False)

    creator:      Mapped["User"]       = relationship("User", foreign_keys=[creator_id])
    participants: Mapped[list["User"]] = relationship(
        "User", secondary=event_participants, lazy="selectin"
    )

    def serialize(self):
        return {
            "id":                 self.id,
            "date":               self.date,
            "time":               self.time,
            "location":           self.location,
            "latitude":           self.latitude,
            "longitude":          self.longitude,
            "details":            self.details,
            "image":              self.image,
            "creator_id":         self.creator_id,
            "creator_email":      self.creator.email,
            "participants":       [{"id": p.id, "email": p.email} for p in self.participants],
            "participants_count": len(self.participants),
        }


# ── FRIENDSHIP ────────────────────────────────────────────
class Friendship(db.Model):
    __tablename__ = "friendship"

    id:           Mapped[int] = mapped_column(primary_key=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    addressee_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    status:       Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at:   Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at:   Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id])
    addressee: Mapped["User"] = relationship("User", foreign_keys=[addressee_id])

    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="uq_friendship_pair"),
        CheckConstraint("requester_id <> addressee_id", name="ck_friendship_not_self"),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'refused')",
            name="ck_friendship_status",
        ),
    )

    def serialize(self, current_user_id=None):
        data = {
            "id":           self.id,
            "requester_id": self.requester_id,
            "addressee_id": self.addressee_id,
            "status":       self.status,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "updated_at":   self.updated_at.isoformat() if self.updated_at else None,
            "requester":    {"id": self.requester.id, "email": self.requester.email} if self.requester else None,
            "addressee":    {"id": self.addressee.id, "email": self.addressee.email} if self.addressee else None,
        }
        if current_user_id is not None:
            other = self.addressee if self.requester_id == current_user_id else self.requester
            data["friend"]    = {"id": other.id, "email": other.email} if other else None
            data["direction"] = "outgoing" if self.requester_id == current_user_id else "incoming"
        return data


# ── CHAT & NOTIFICATIONS ─────────────────────────────────
class NotificationType(str, Enum):
    NEW_MESSAGE     = "new_message"
    MATCH           = "match"
    EVENT_UPDATE    = "event_update"
    EVENT_CANCELLED = "event_cancelled"
    FRIEND_REQUEST  = "friend_request"
    FRIEND_ACCEPTED = "friend_accepted"


class Conversation(db.Model):
    """
    Conversación 1-a-1 ligada a un evento.
    user1_id < user2_id siempre (normalizado en el helper) para que la
    UniqueConstraint funcione y no haya conversaciones duplicadas.
    """
    __tablename__ = "conversation"
    __table_args__ = (
        UniqueConstraint("event_id", "user1_id", "user2_id", name="uq_conversation_event_pair"),
    )

    id:         Mapped[int] = mapped_column(primary_key=True)
    event_id:   Mapped[int] = mapped_column(ForeignKey("event.id"), nullable=False)
    user1_id:   Mapped[int] = mapped_column(ForeignKey("user.id"),  nullable=False)
    user2_id:   Mapped[int] = mapped_column(ForeignKey("user.id"),  nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user1: Mapped["User"] = relationship("User", foreign_keys=[user1_id])
    user2: Mapped["User"] = relationship("User", foreign_keys=[user2_id])

    messages: Mapped[List["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def other_user(self, current_user_id: int) -> "User":
        return self.user2 if self.user1_id == current_user_id else self.user1

    def other_user_id(self, current_user_id: int) -> int:
        return self.user2_id if self.user1_id == current_user_id else self.user1_id

    def has_participant(self, user_id: int) -> bool:
        return user_id in (self.user1_id, self.user2_id)

    def serialize(self, current_user_id: Optional[int] = None):
        data = {
            "id":           self.id,
            "event_id":     self.event_id,
            "participants": [self.user1_id, self.user2_id],
            "created_at":   self.created_at.isoformat() if self.created_at else None,
        }
        if current_user_id is not None:
            other = self.other_user(current_user_id)
            data["other_user_id"] = other.id
            data["other_user"]    = other.public_brief() if other else None
            data["unread_count"]  = sum(
                1 for m in self.messages if not m.is_read and m.sender_id != current_user_id
            )
            last = self.messages[-1] if self.messages else None
            data["last_message"] = last.serialize() if last else None
        return data


class Message(db.Model):
    __tablename__ = "message"
    __table_args__ = (
        Index("ix_message_conversation_created", "conversation_id", "created_at"),
    )

    id:              Mapped[int]  = mapped_column(primary_key=True)
    conversation_id: Mapped[int]  = mapped_column(ForeignKey("conversation.id"), nullable=False)
    sender_id:       Mapped[int]  = mapped_column(ForeignKey("user.id"),         nullable=False)
    content:         Mapped[str]  = mapped_column(Text, nullable=False)
    is_read:         Mapped[bool] = mapped_column(Boolean, default=False)
    created_at:      Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")

    def serialize(self):
        return {
            "id":              self.id,
            "conversation_id": self.conversation_id,
            "sender_id":       self.sender_id,
            "content":         self.content,
            "is_read":         self.is_read,
            "created_at":      self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notification"
    __table_args__ = (
        Index("ix_notification_user_unread", "user_id", "is_read"),
    )

    id:         Mapped[int] = mapped_column(primary_key=True)
    user_id:    Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False)
    type:       Mapped[NotificationType] = mapped_column(SAEnum(NotificationType), nullable=False)
    message:    Mapped[str] = mapped_column(String(255), nullable=False)
    related_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    is_read:    Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def serialize(self):
        return {
            "id":         self.id,
            "user_id":    self.user_id,
            "type":       self.type.value,
            "message":    self.message,
            "related_id": self.related_id,
            "is_read":    self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }