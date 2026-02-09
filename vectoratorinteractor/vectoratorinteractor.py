import json
from datetime import datetime
from typing import List, Optional

import requests
from fastapi import HTTPException, UploadFile

from vectoratorinteractor.models import (
    ChatCreate,
    ChatMessageResponse,
    ChatMessageWithDocumentsPD,
    ChatResponse,
    ChatWithMessagesPD,
    DocumentResponse,
    DocumentUploadRequest,
    DocumentUploadRequestWithDocumentsPD,
    FullDocumentWithPreview,
    MemoryResponse,
    MessageCreate,
    NewMessagePD,
    Persona,
    ProcessingState,
    ProjectCreate,
    ProjectResponse,
    QuickSearchDocument,
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
    # Legacy/compat document & file helpers
    # -------------------------------------------------------------------------

    def uploadDocuments(
        self,
        project: str,
        files: List[UploadFile],
        apporuser: str = "",
        highresmode: bool = False,  # kept for signature compatibility; ignored
    ) -> DocumentUploadRequest:
        """
        Backwards-compatible multi-file upload helper.

        Internally calls the single-file /api/v1 upload endpoint once per file
        and aggregates the results into a DocumentUploadRequest-like object.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)

        uploaded_docs: List[FullDocumentWithPreview] = []
        for f in files:
            doc_resp = self.uploadDocument(
                project=project,
                file=f,
                apporuser=apporuser,
                display_name=f.filename,
            )
            uploaded_docs.append(
                FullDocumentWithPreview(
                    id=doc_resp.id,
                    filename=doc_resp.file_name,
                    apporuser=username,
                    project_id=doc_resp.project_id,
                    upload_request_id=0,
                    cover_url=None,
                    zoomed_in_url=None,
                )
            )

        now = None
        upload_request = DocumentUploadRequest(
            id=None,
            apporuser=username,
            project=project,
            processed=True,
            created_at=now,
            errormessage=None,
        )

        # For callers that used getUploadRequests/getUploadRequestById, we at
        # least provide a single synthetic request containing all docs.
        self._last_upload_request = DocumentUploadRequestWithDocumentsPD(
            id=0,
            apporuser=username,
            project=project,
            processed=True,
            created_at=now or now,
            errormessage=None,
            documents=uploaded_docs,
        )

        return upload_request

    def getUploadRequests(
        self, project: str, apporuser: str = ""
    ) -> List[DocumentUploadRequestWithDocumentsPD]:
        """
        Compatibility stub for old upload request listing.

        The new backend no longer exposes upload-request entities, so we return
        at most the last synthetic request created via uploadDocuments().
        """
        if hasattr(self, "_last_upload_request"):
            return [self._last_upload_request]  # type: ignore[attr-defined]
        return []

    def getUploadRequestById(
        self, project: str, uploadrequest_id: int, apporuser: str = ""
    ) -> DocumentUploadRequestWithDocumentsPD:
        """
        Compatibility stub for fetching a single upload request.
        """
        for req in self.getUploadRequests(project, apporuser):
            if req.id == uploadrequest_id:
                return req
        raise HTTPException(status_code=404, detail="Upload request not found")

    def listFiles(self, project: str, apporuser: str = "") -> List[str]:
        """
        Legacy helper that returns just the filenames for a project's documents.
        """
        docs = self.getDocuments(project, apporuser=apporuser)
        return [d.file_name for d in docs]

    def getPresignedUrl(
        self, project: str, filename: str, apporuser: str = "", validity_days: int = 7
    ) -> str:
        """
        The new FastAPI backend exposes preview/download endpoints instead of
        raw S3 presigned URLs; this method is no longer backed by the service.
        """
        raise HTTPException(
            status_code=501,
            detail="getPresignedUrl is not implemented against the new /api/v1 backend.",
        )

    def getPdfPagePicture(
        self, project: str, pdffilename: str, page: int, apporuser: str = ""
    ) -> str:
        raise HTTPException(
            status_code=501,
            detail="getPdfPagePicture is not implemented against the new /api/v1 backend.",
        )

    def getCoverForBook(self, project: str, filename: str, apporuser: str = "") -> str:
        raise HTTPException(
            status_code=501,
            detail="getCoverForBook is not implemented against the new /api/v1 backend.",
        )

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
    # Legacy/compat chat & Q&A helpers
    # -------------------------------------------------------------------------

    def getChatStatus(
        self, project: str, chat_id: int, apporuser: str = ""
    ) -> ProcessingState:
        """
        Legacy status helper. The new backend answers synchronously, so we
        simply report DONE for any known chat id and raise if not found.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        url = f"{self._api_v1_base}/users/{username}/projects/{project}/chats"
        response = requests.get(url, params={"limit": 100, "offset": 0})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        chats = response.json()
        if any(c.get("id") == chat_id for c in chats):
            return ProcessingState.DONE
        raise HTTPException(status_code=404, detail="Chat not found")

    def addMessage(
        self, project: str, chat_id: int, message: NewMessagePD, apporuser: str = ""
    ) -> ChatWithMessagesPD:
        """
        Compatibility wrapper that sends a message by chat id using the
        name-based /api/v1 messages endpoint and maps the result to
        ChatWithMessagesPD.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)
        # Resolve chat_name from id
        chats = self.getChats(project, apporuser=apporuser)
        chat = next((c for c in chats if c.id == chat_id), None)
        if chat is None:
            raise HTTPException(status_code=404, detail="Chat not found")

        content = message.message
        resp = self.sendMessage(
            project=project,
            chatname=chat.chat_name,
            content=content,
            apporuser=apporuser,
            stream=False,
        )

        return self._chat_from_message_response(
            username=username,
            project=project,
            chat_name=chat.chat_name,
            chat_id=chat.id,
            msg_resp=resp,
        )

    def questionWaitUntilFinished(
        self, project: str, question: str, apporuser: str = "", chat_id: int | None = None
    ) -> ChatWithMessagesPD:
        """
        Legacy \"ask a question and wait\" helper.

        The new backend answers synchronously, so we send a single message and
        immediately return a ChatWithMessagesPD with processing_state=DONE.
        """
        username = self.__getOrRaiseApporuserConstructor(apporuser)

        if chat_id is None:
            # Create a new chat with a generated name
            chat_name = f"chat-{datetime.utcnow().isoformat()}"
            chat = self.createChat(project=project, chatname=chat_name, apporuser=apporuser)
            chat_id = chat.id
        else:
            # Resolve chat name from id
            chats = self.getChats(project, apporuser=apporuser)
            chat = next((c for c in chats if c.id == chat_id), None)
            if chat is None:
                raise HTTPException(status_code=404, detail="Chat not found")
            chat_name = chat.chat_name

        msg = NewMessagePD(message=question, persona=Persona.user)
        resp = self.sendMessage(
            project=project,
            chatname=chat_name,
            content=msg.message,
            apporuser=apporuser,
            stream=False,
        )

        return self._chat_from_message_response(
            username=username,
            project=project,
            chat_name=chat_name,
            chat_id=chat_id,
            msg_resp=resp,
        )

    def _chat_from_message_response(
        self,
        username: str,
        project: str,
        chat_name: str,
        chat_id: int,
        msg_resp: ChatMessageResponse,
    ) -> ChatWithMessagesPD:
        """
        Helper to build a legacy ChatWithMessagesPD from a ChatMessageResponse.
        """
        user = msg_resp.user_message
        bot = msg_resp.bot_message

        user_msg_pd = ChatMessageWithDocumentsPD(
            id=user.id,
            message=user.content,
            persona=Persona.user,
            created_at=user.created_at,
            documents=[],
        )
        bot_msg_pd = ChatMessageWithDocumentsPD(
            id=bot.id,
            message=bot.content,
            persona=Persona.assistant,
            created_at=bot.created_at,
            documents=[],
        )

        return ChatWithMessagesPD(
            id=chat_id,
            name=chat_name,
            apporuser=username,
            project=project,
            created_at=user.created_at,
            processing_state=ProcessingState.DONE,
            messages=[user_msg_pd, bot_msg_pd],
        )

    def quicksearch(
        self, project: str, query: str, apporuser: str = ""
    ) -> List[QuickSearchDocument]:
        """
        Legacy quicksearch helper.

        The current backend does not expose a direct quicksearch endpoint;
        callers should migrate to RAG chat instead. This method is kept only
        for API compatibility and always raises 501.
        """
        raise HTTPException(
            status_code=501,
            detail="quicksearch is not implemented against the new /api/v1 backend.",
        )

    # Stream helpers from the old API are not available on the new backend.

    def stream_answer(self, apporuser: str, project: str, messages: list[NewMessagePD]):
        raise HTTPException(
            status_code=501,
            detail="stream_answer is not implemented against the new /api/v1 backend.",
        )

    def stream_answer_tokens(
        self, apporuser: str, project: str, messages: list[NewMessagePD]
    ):
        raise HTTPException(
            status_code=501,
            detail="stream_answer_tokens is not implemented against the new /api/v1 backend.",
        )

    def stream_answer_events(
        self, apporuser: str, project: str, messages: list[NewMessagePD]
    ):
        raise HTTPException(
            status_code=501,
            detail="stream_answer_events is not implemented against the new /api/v1 backend.",
        )

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
