from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import ForeignKey, Text
from sqlmodel import Column, Field, Relationship, SQLModel


def _utc_now() -> datetime:
    """Current UTC time."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Core enums used by both DB models and API schemas
# ---------------------------------------------------------------------------


class MessageRole(str, Enum):
    USER = "user"
    BOT = "bot"


class ProcessingState(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Persona(str, Enum):
    assistant = "assistant"
    user = "user"


# ---------------------------------------------------------------------------
# Database models (used by the FastAPI backend, unchanged)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Legacy Pydantic API models (compatibility with older vectoratorinteractor)
# ---------------------------------------------------------------------------


class NewMessagePD(BaseModel):
    message: str
    persona: Persona


class DocumentUploadRequest(BaseModel):
    """Compatibility-only representation of an upload request."""

    id: Optional[int] = None
    apporuser: str
    project: str
    processed: bool = False
    created_at: datetime | None = None
    errormessage: str | None = None


class FullDocumentWithPreview(BaseModel):
    id: int | None = None
    filename: str
    apporuser: str
    project_id: int
    upload_request_id: int
    cover_url: str | None = None
    zoomed_in_url: str | None = None


class LangchainDocumentPD(BaseModel):
    id: UUID
    filename: str
    filetype: str
    source: str
    content: str
    url: str
    cover_url: str
    zoomed_in_url: str | None = None
    page_number: int | None = None


class QuickSearchDocument(BaseModel):
    score: int
    filename: str
    content: str
    fullcontent: str
    timestamp: str


class ChatMessageWithDocumentsPD(BaseModel):
    id: int
    message: str
    persona: Persona
    created_at: datetime
    documents: List[LangchainDocumentPD] = []


class ChatWithMessagesPD(BaseModel):
    id: int
    name: str
    apporuser: str
    project: str
    created_at: datetime
    processing_state: ProcessingState
    messages: List[ChatMessageWithDocumentsPD] = []


class NewChatPD(BaseModel):
    name: str
    apporuser: str
    project: str
    messages: List["ChatMessageWithDocumentsPD"] = []


class DocumentUploadRequestWithDocumentsPD(BaseModel):
    id: int
    apporuser: str
    project: str
    processed: bool
    created_at: datetime
    errormessage: str | None = None
    documents: List[FullDocumentWithPreview] = []


# ---------------------------------------------------------------------------
# Pydantic schemas mirroring the new FastAPI /api/v1 backend
# (used by the HTTP wrapper in vectoratorinteractor.py)
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    project_name: str


class ProjectResponse(BaseModel):
    id: int
    username: str
    project_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    display_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    cover_image_data: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ChatCreate(BaseModel):
    chat_name: str


class ChatResponse(BaseModel):
    id: int
    username: str
    project_name: str
    project_id: int
    chat_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CitationResponse(BaseModel):
    id: int
    document_id: int
    file_name: str
    chunk_text: Optional[str]
    start_index: Optional[int]
    end_index: Optional[int]
    preview_url: str
    download_url: str

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    role: MessageRole
    content: str
    created_at: datetime
    citations: List[CitationResponse] = []

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    """Response for sending a message - includes bot response with citations."""

    user_message: MessageResponse
    bot_message: MessageResponse


class MemoryResponse(BaseModel):
    key: str
    content: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: str
