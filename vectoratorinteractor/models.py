import enum
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel


class SummaryStore(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    summary: str = Field(nullable=False)


class ProcessingState(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Persona(enum.Enum):
    agent = "agent"
    user = "user"


class ChatMessageDocument(SQLModel, table=True):
    chat_message_id: int = Field(foreign_key="chatmessage.id", primary_key=True)
    document_id: int = Field(foreign_key="document.id", primary_key=True)


class QuestionDocument(SQLModel, table=True):
    question_id: int = Field(foreign_key="questionsstore.id", primary_key=True)
    document_id: int = Field(foreign_key="document.id", primary_key=True)


class Project(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(nullable=False)
    apporuser: str = Field(nullable=False)
    document_upload_requests: List["DocumentUploadRequest"] = Relationship(
        back_populates="project"
    )
    chats: List["Chat"] = Relationship(back_populates="project")
    documents: List["Document"] = Relationship(back_populates="project")


class QuestionsStore(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, primary_key=True
    )  # Ensure primary key is defined
    question: str = Field(index=True, nullable=False)
    answer: Optional[str] = Field(default=None)
    apporuser: str = Field(index=True, nullable=False)
    documents: List["Document"] = Relationship(
        back_populates="questions", link_model=QuestionDocument
    )


class Chat(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(default="new chat", nullable=False)
    apporuser: str = Field(nullable=False, index=True)
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="chats")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    processing_state: ProcessingState = Field(
        nullable=False, default=ProcessingState.DONE
    )
    messages: List["ChatMessage"] = Relationship(back_populates="chat")


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    message: str = Field(nullable=False)
    persona: Persona = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    chat_id: Optional[int] = Field(default=None, foreign_key="chat.id")
    chat: Optional[Chat] = Relationship(back_populates="messages")
    documents: List["Document"] = Relationship(
        back_populates="chat_messages", link_model=ChatMessageDocument
    )


class DocumentUploadRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    apporuser: str = Field(nullable=False, index=True)
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="document_upload_requests")
    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    documents: List["Document"] = Relationship(back_populates="upload_request")


class Document(SQLModel, table=True):
    id: Optional[int] = Field(
        default=None, primary_key=True
    )  # Ensure primary key is defined
    filename: str = Field(nullable=False)
    apporuser: str = Field(nullable=False, index=True)
    project_id: int = Field(foreign_key="project.id")
    project: Project = Relationship(back_populates="documents")
    upload_request_id: int = Field(foreign_key="documentuploadrequest.id")
    upload_request: DocumentUploadRequest = Relationship(back_populates="documents")
    chat_messages: List["ChatMessage"] = Relationship(
        back_populates="documents", link_model=ChatMessageDocument
    )
    questions: List["QuestionsStore"] = Relationship(
        back_populates="documents", link_model=QuestionDocument
    )


class ChatWithMessagesPD(BaseModel):
    id: int
    name: str
    apporuser: str
    project: str
    created_at: datetime
    processing_state: ProcessingState
    messages: List[ChatMessage] = []


class NewChatPD(BaseModel):
    name: str
    apporuser: str
    project: str
    messages: List[ChatMessage] = []
