import enum
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class ProcessingState(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Persona(enum.Enum):
    assistant = "assistant"
    user = "user"


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    apporuser: str = Field(nullable=False)
    document_upload_requests: List["DocumentUploadRequest"] = Relationship(
        back_populates="project"
    )
    chats: List["Chat"] = Relationship(back_populates="project")
    documents: List["FullDocument"] = Relationship(back_populates="project")


class QuestionsStore(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, primary_key=True
    )  # Ensure primary key is defined
    question: str = Field(index=True, nullable=False)
    answer: Optional[str] = Field(default=None)
    apporuser: str = Field(nullable=False, index=True)
    langchain_document_ids: List[str] = Field(
        sa_column=Column(JSON, nullable=False, default=list)
    )


class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="new chat", nullable=False)
    apporuser: str = Field(nullable=False, index=True)
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="chats")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    processing_state: ProcessingState = Field(
        nullable=False, default=ProcessingState.DONE
    )
    messages: List["ChatMessage"] = Relationship(back_populates="chat")
    errormessage: str | None = Field(default=None)


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str = Field(nullable=False)
    persona: Persona = Field(nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    chat_id: Optional[int] = Field(default=None, foreign_key="chat.id")
    chat: Optional[Chat] = Relationship(back_populates="messages")
    langchain_document_ids: List[str] = Field(
        sa_column=Column(JSON, nullable=False, default=list)
    )


class NewMessagePD(BaseModel):
    message: str
    persona: Persona


class DocumentUploadRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apporuser: str = Field(nullable=False, index=True)
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="document_upload_requests")
    processed: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), nullable=False
    )
    errormessage: str | None = Field(default=None)
    documents: List["FullDocument"] = Relationship(back_populates="upload_request")


class DocumentUploadRequestWithDocumentsPD(BaseModel):
    id: int
    apporuser: str
    project: str
    processed: bool
    created_at: datetime
    errormessage: str | None = None
    documents: List["FullDocument"] = []


class FullDocument(SQLModel, table=True):
    id: int | None = Field(
        default=None, primary_key=True
    )  # Ensure primary key is defined
    filename: str = Field(nullable=False)  # == source

    apporuser: str = Field(nullable=False, index=True)
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="documents")
    upload_request_id: int = Field(foreign_key="documentuploadrequest.id")
    upload_request: DocumentUploadRequest = Relationship(back_populates="documents")


class LangchainDocumentPD(BaseModel):
    id: UUID
    filename: str
    filetype: str
    source: str
    content: str
    # summary: str
    url: str
    cover_url: str
    zoomed_in_url: str | None = None
    page_number: int | None = None


class QuickSearchDocument(BaseModel):
    score: int
    filename: str
    content: str
    fullcontent: str
    # summary: str
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
    messages: List[ChatMessage] = []
