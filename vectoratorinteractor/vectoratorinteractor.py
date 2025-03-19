import enum
from datetime import datetime
from typing import Dict, List, Optional

import requests
from fastapi import UploadFile
from pydantic import BaseModel
from sqlmodel import JSON, Column, Field, Relationship, SQLModel


class SummaryStore(SQLModel, table=True):
    id: str | None = Field(default=None, primary_key=True)
    summary: str = Field(nullable=False)


class ProcessingState(enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    DONE = "DONE"
    FAILED = "FAILED"


class Persona(enum.Enum):
    agent = "agent"
    user = "user"


class QuestionsStore(SQLModel, table=True):
    question: str = Field(primary_key=True, index=True, nullable=False)
    message_id: Optional[int] = Field(default=None, foreign_key="chatmessage.id")
    answer: Optional[str] = Field(default=None)
    message: Optional["ChatMessage"] = Relationship()
    project: str = Field(primary_key=True, index=True, nullable=False)
    apporuser: str = Field(primary_key=True, index=True, nullable=False)
    source_documents: Dict | None = Field(default_factory=dict, sa_column=Column(JSON))


class Chat(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(default="new chat", nullable=False)
    apporuser: str = Field(nullable=False)
    project: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    processing_state: ProcessingState = Field(
        nullable=False,
        default=ProcessingState.DONE,
    )
    messages: list["ChatMessage"] = Relationship(back_populates="chat")


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    chat_id: int | None = Field(default=None, foreign_key="chat.id")
    chat: Chat | None = Relationship(back_populates="messages")
    message: str = Field(nullable=False)
    persona: Persona = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    source_documents: Dict | None = Field(default_factory=dict, sa_column=Column(JSON))


class ChatWithMessages(BaseModel):
    id: int
    name: str
    apporuser: str
    project: str
    created_at: datetime
    processing_state: ProcessingState
    messages: List[ChatMessage] = []


class NewChat(BaseModel):
    name: str
    apporuser: str
    project: str
    messages: List[ChatMessage] = []


class VectoratorInteractor:
    def __init__(
        self,
        mainappname: str,
        vectoratorurl: str = "http://vectorator-service.vectorator.svc.cluster.local:8000",
    ):
        self.mainappname = mainappname
        self.vectoratorurl = vectoratorurl

    def uploadDocuments(
        self,
        apporuser: str,
        project: str,
        files: List[UploadFile],
        highresmode: bool = False,
    ):
        url = (
            self.vectoratorurl
            + f"/upload/{self.mainappname + "_" + apporuser}/{project}"
        )
        newFiles = []
        for f in files:
            newFiles.append(("upload_files", (f.filename, f.file, f.content_type)))

        response = requests.post(
            url, files=newFiles, params={"highresmode": highresmode}
        )
        response.raise_for_status()

    def getPresignedUrl(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/presigned_url/{self.mainappname + "_" + apporuser}/{project}/{filename}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.text.replace('"', "")

    def getCoverForBook(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/presigned_url/{self.mainappname + "_" + apporuser}/{project}/{filename + '.png'}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.text.replace('"', "")

    def deleteProjectFromBackend(self, apporuser: str, project: str):
        url = self.vectoratorurl + f"/{self.mainappname + "_" + apporuser}/{project}"
        response = requests.delete(url)
        response.raise_for_status()

    def quicksearch(self, apporuser: str, project: str, query: str) -> ChatMessage:
        url = (
            self.vectoratorurl
            + f"/quicksearch/{self.mainappname + "_" + apporuser}/{project}/{query}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return ChatMessage(**response.json())

    ### Chat routes
    def getChats(self, apporuser: str, project: str) -> List[ChatWithMessages]:
        url = (
            self.vectoratorurl + f"/chat/{self.mainappname + "_" + apporuser}/{project}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return [ChatWithMessages(**chat) for chat in response.json()]

    def getChat(self, apporuser: str, project: str, chat_id: int) -> ChatWithMessages:
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/{chat_id}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return ChatWithMessages(**response.json())

    def createChat(self, chat: NewChat) -> ChatWithMessages:
        url = self.vectoratorurl + f"/chat/"
        response = requests.post(url, json=chat.model_dump())
        response.raise_for_status()
        return ChatWithMessages(**response.json())

    def addMessage(
        self, apporuser: str, project: str, message: ChatMessage
    ) -> ChatWithMessages:
        url = (
            self.vectoratorurl
            + f"/chat/message/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.put(url, json=message.model_dump())
        response.raise_for_status()
        return ChatWithMessages(**response.json())

    def deleteChat(self, apporuser: str, project: str, chat_id: int):
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/{chat_id}"
        )
        response = requests.delete(url)
        response.raise_for_status()

    # simplified question route
    def question(
        self, apporuser: str, project: str, question: str, chat_id: int = None
    ) -> ChatWithMessages:
        if chat_id is not None:
            self.addMessage(
                apporuser,
                project,
                ChatMessage(chat_id=chat_id, message=question, persona=Persona.user),
            )
            chat = self.getChat(apporuser, project, chat_id)
        else:
            newChat = NewChat(
                apporuser=apporuser,
                project=project,
                messages=[ChatMessage(message=question, persona=Persona.user)],
            )
            chat = self.createChat(newChat)
        maxtries = 30
        crntTry = 0
        while chat.processing_state != ProcessingState.DONE and crntTry < maxtries:
            chat = self.getChat(apporuser, project, chat.id)
            maxtries -= 1
        assert chat.processing_state == ProcessingState.DONE
        return chat
