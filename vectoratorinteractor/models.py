from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Text
from sqlmodel import Column, Field, Relationship, SQLModel


def _utc_now() -> datetime:
    """Current UTC time (replaces deprecated _utc_now())."""
    return datetime.now(timezone.utc)


class MessageRole(str, Enum):
    USER = "user"
    BOT = "bot"


class User(SQLModel, table=True):
    __tablename__ = "users"

    username: str = Field(primary_key=True, index=True)
    created_at: datetime = Field(default_factory=_utc_now)


class Project(SQLModel, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(foreign_key="users.username", index=True)
    project_name: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    # Relationships
    documents: list["Document"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    chats: list["Chat"] = Relationship(
        back_populates="project",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    class Config:
        unique_together = [("username", "project_name")]


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(
        sa_column=Column(
            ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    file_name: str  # Original filename
    display_name: str  # Display name for citations
    file_size: Optional[int] = None  # Size in bytes
    mime_type: Optional[str] = None
    s3_object_key: Optional[str] = None
    cover_image_data: Optional[str] = Field(default=None, sa_column=Column(Text))
    created_at: datetime = Field(default_factory=_utc_now)

    # Relationships
    project: Project = Relationship(back_populates="documents")
    citations: list["Citation"] = Relationship(
        back_populates="document",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    project_name: str = Field(index=True)
    project_id: int = Field(
        sa_column=Column(
            ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    chat_name: str = Field(index=True)
    created_at: datetime = Field(default_factory=_utc_now)
    updated_at: datetime = Field(default_factory=_utc_now)

    # Relationships
    project: Project = Relationship(back_populates="chats")
    messages: list["Message"] = Relationship(
        back_populates="chat",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )

    class Config:
        unique_together = [("username", "project_name", "chat_name")]


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(
        sa_column=Column(
            ForeignKey("chats.id", ondelete="CASCADE"),
            index=True,
            nullable=False,
        )
    )
    role: MessageRole
    content: str
    created_at: datetime = Field(default_factory=_utc_now)

    # Relationships
    chat: Chat = Relationship(back_populates="messages")
    citations: list["Citation"] = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class Citation(SQLModel, table=True):
    __tablename__ = "citations"

    id: Optional[int] = Field(default=None, primary_key=True)
    message_id: int = Field(
        sa_column=Column(
            ForeignKey("messages.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    document_id: int = Field(
        sa_column=Column(
            ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    chunk_text: Optional[str] = None  # The text chunk that was cited
    file_name: str  # File name from citation
    start_index: Optional[int] = None  # Start index in document
    end_index: Optional[int] = None  # End index in document

    # Relationships
    message: Message = Relationship(back_populates="citations")
    document: Document = Relationship(back_populates="citations")
