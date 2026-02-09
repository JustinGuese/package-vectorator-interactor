import json
from typing import List, Optional

import requests
from fastapi import HTTPException, UploadFile

from vectoratorinteractor.models import (
    ChatCreate,
    ChatMessageResponse,
    ChatResponse,
    DocumentResponse,
    MemoryResponse,
    MessageCreate,
    ProjectCreate,
    ProjectResponse,
)


class VectoratorInteractor:
    def __init__(
        self,
        mainappname: str = "vinteractor",
        apporuserdefault: str = "",
        vectoratorurl: str = "http://vectorator-service.vectorator.svc.cluster.local:8000",
    ):
        self.mainappname = mainappname
        self.vectoratorurl = vectoratorurl
        self.apporuserdefault = apporuserdefault

    @property
    def _api_v1_base(self) -> str:
        """Base URL for the FastAPI v1 routes."""
        return self.vectoratorurl.rstrip("/") + "/api/v1"

    def __getOrRaiseApporuserConstructor(self, apporuser: str) -> str:
        """
        Historical helper: build the username path segment from mainapp/apporuser.

        We continue to keep this behaviour so existing callers don't need to
        change anything – the resulting value is used as the FastAPI `username`.
        """
        if (
            apporuser == ""
            and self.mainappname == "vinteractor"
            and self.apporuserdefault == ""
        ):
            raise ValueError(
                "if self.mainappname and self.apporuserdefault are default you have to pass apporuser!"
            )
        elif apporuser is not None and apporuser != "":
            return self.mainappname + "_" + apporuser
        else:
            return self.mainappname + "_" + self.apporuserdefault

    # -------------------------------------------------------------------------
    # Project operations
    # -------------------------------------------------------------------------

    def getProjects(self, apporuser: str) -> List[str]:
        """
        List projects for the (derived) username.

        Backed by: GET /api/v1/users/{username}/projects
        Returns only the project_name values to keep the old, simple return type.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects"
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [p["project_name"] for p in response.json()]

    def createProject(self, project: str, apporuser: str = "") -> ProjectResponse:
        """
        Create a new project for the (derived) username.

        Backed by: POST /api/v1/users/{username}/projects
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects"
        payload = ProjectCreate(project_name=project)
        response = requests.post(url, json=json.loads(payload.model_dump_json()))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ProjectResponse(**response.json())

    def deleteProjectFromBackend(self, project: str, apporuser: str = "") -> None:
        """
        Delete a project for the (derived) username.

        Backed by: DELETE /api/v1/users/{username}/projects/{project_name}
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}"
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    # -------------------------------------------------------------------------
    # Document operations
    # -------------------------------------------------------------------------

    def uploadDocument(
        self,
        project: str,
        file: UploadFile,
        apporuser: str = "",
        display_name: Optional[str] = None,
    ) -> DocumentResponse:
        """
        Upload a single document to a project.

        Backed by: POST /api/v1/users/{username}/projects/{project_name}/documents

        Note: the legacy API supported multi-file uploads and various upload
        request helpers; the new FastAPI app exposes a single-file upload
        endpoint, so this wrapper now mirrors that behaviour.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/documents"

        files = {"file": (file.filename, file.file, file.content_type)}
        data: dict = {}
        if display_name is not None:
            data["display_name"] = display_name

        response = requests.post(url, files=files, data=data)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return DocumentResponse(**response.json())

    def getDocuments(
        self, project: str, apporuser: str = "", limit: int = 50, offset: int = 0
    ) -> List[DocumentResponse]:
        """
        List documents for a project.

        Backed by: GET /api/v1/users/{username}/projects/{project_name}/documents
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/documents"
        response = requests.get(url, params={"limit": limit, "offset": offset})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [DocumentResponse(**doc) for doc in response.json()]

    def getDocumentById(
        self, project: str, document_id: int, apporuser: str = ""
    ) -> DocumentResponse:
        """
        Get a single document by ID.

        Backed by:
          GET /api/v1/users/{username}/projects/{project_name}/documents/{document_id}
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/documents/"
            f"{document_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return DocumentResponse(**response.json())

    def deleteDocumentById(
        self, project: str, document_id: int, apporuser: str = ""
    ) -> None:
        """
        Delete a document by ID.

        Backed by:
          DELETE /api/v1/users/{username}/projects/{project_name}/documents/{document_id}
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/documents/"
            f"{document_id}"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    # -------------------------------------------------------------------------
    # Chat & message routes
    # -------------------------------------------------------------------------

    def getChats(
        self, project: str, apporuser: str = "", limit: int = 50, offset: int = 0
    ) -> List[ChatResponse]:
        """
        List chats for a project.

        Backed by: GET /api/v1/users/{username}/projects/{project_name}/chats
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/chats"
        response = requests.get(url, params={"limit": limit, "offset": offset})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [ChatResponse(**chat) for chat in response.json()]

    def createChat(
        self, project: str, chatname: str, apporuser: str = ""
    ) -> ChatResponse:
        """
        Create a chat in a project.

        Backed by: POST /api/v1/users/{username}/projects/{project_name}/chats
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/chats"
        payload = ChatCreate(chat_name=chatname)
        response = requests.post(url, json=json.loads(payload.model_dump_json()))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatResponse(**response.json())

    def getChat(
        self, project: str, chatname: str, apporuser: str = ""
    ) -> ChatResponse:
        """
        Get a single chat (metadata only).

        Backed by:
          GET /api/v1/users/{username}/projects/{project_name}/chats/{chat_name}
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/chats/{chatname}"
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatResponse(**response.json())

    def deleteChat(self, project: str, chatname: str, apporuser: str = "") -> None:
        """
        Delete a chat.

        Backed by:
          DELETE /api/v1/users/{username}/projects/{project_name}/chats/{chat_name}
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/chats/{chatname}"
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def sendMessage(
        self,
        project: str,
        chatname: str,
        content: str,
        apporuser: str = "",
        stream: bool = False,
    ) -> ChatMessageResponse | requests.Response:
        """
        Send a message to a chat and get a bot response.

        Backed by:
          POST /api/v1/users/{username}/projects/{project_name}/chats/{chat_name}/messages?stream=...

        If `stream=True`, the raw `requests.Response` is returned so callers can
        iterate over the NDJSON stream (`iter_lines`, etc.). Otherwise, this
        returns a parsed `ChatMessageResponse`.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/chats/"
            f"{chatname}/messages"
        )
        payload = MessageCreate(content=content)

        if stream:
            response = requests.post(
                url,
                params={"stream": "true"},
                json=json.loads(payload.model_dump_json()),
                stream=True,
            )
            if not response.ok:
                raise HTTPException(
                    status_code=response.status_code, detail=response.text
                )
            return response

        response = requests.post(
            url,
            params={"stream": "false"},
            json=json.loads(payload.model_dump_json()),
        )
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatMessageResponse(**response.json())

    def getMessages(
        self,
        project: str,
        chatname: str,
        apporuser: str = "",
        limit: int = 50,
        offset: int = 0,
    ):
        """
        Get messages for a chat with citations.

        Backed by:
          GET /api/v1/users/{username}/projects/{project_name}/chats/{chat_name}/messages
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/chats/"
            f"{chatname}/messages"
        )
        response = requests.get(url, params={"limit": limit, "offset": offset})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        # We intentionally return the raw JSON list so callers can decide how to
        # map it (it matches the backend's `MessageResponse` schema).
        return response.json()

    # -------------------------------------------------------------------------
    # Long‑term memories
    # -------------------------------------------------------------------------

    def listMemories(
        self,
        project: str,
        apporuser: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> List[MemoryResponse]:
        """
        List long‑term memories for a project.

        Backed by:
          GET /api/v1/users/{username}/projects/{project_name}/memories
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/memories"
        )
        response = requests.get(url, params={"limit": limit, "offset": offset})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [MemoryResponse(**item) for item in response.json()]

    def searchMemories(
        self,
        project: str,
        query: str,
        apporuser: str = "",
        limit: int = 10,
    ) -> List[MemoryResponse]:
        """
        Semantic search over memories for a project.

        Backed by:
          POST /api/v1/users/{username}/projects/{project_name}/memories/search
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/memories/search"
        )
        body = {"query": query}
        response = requests.post(url, json=body, params={"limit": limit})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [MemoryResponse(**item) for item in response.json()]

    def deleteMemory(
        self, project: str, memory_key: str, apporuser: str = ""
    ) -> None:
        """
        Delete a specific memory by key.

        Backed by:
          DELETE /api/v1/users/{username}/projects/{project_name}/memories/{memory_key}
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = (
            f"{self._api_v1_base}/users/{username}/projects/{project}/memories/"
            f"{memory_key}"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
