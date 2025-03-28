import json
from datetime import date
from typing import List

import requests
from fastapi import HTTPException, UploadFile

from vectoratorinteractor.models import (
    ChatMessage,
    ChatWithMessagesPD,
    DocumentUploadRequest,
    FullDocument,
    NewChatPD,
    Persona,
    ProcessingState,
    Project,
)


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
            + f"/{self.mainappname + '_' + apporuser}/{project}/upload/"
        )
        newFiles = []
        for f in files:
            newFiles.append(("upload_files", (f.filename, f.file, f.content_type)))

        response = requests.post(
            url, files=newFiles, params={"highresmode": highresmode}
        )
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def getUploadRequests(
        self, apporuser: str, project: str
    ) -> List[DocumentUploadRequest]:
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/uploadrequests"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [DocumentUploadRequest(**req) for req in response.json()]

    def getProjects(self, apporuser: str) -> List[str]:
        url = self.vectoratorurl + f"/projects/{self.mainappname + '_' + apporuser}/"
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def createProject(self, apporuser: str, project: str) -> Project:
        url = self.vectoratorurl + f"/{self.mainappname + '_' + apporuser}/{project}/"
        response = requests.post(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return Project(**response.json())

    def listFiles(self, apporuser: str, project: str) -> List[str]:
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/s3files"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def getPresignedUrl(
        self, apporuser: str, project: str, filename: str, validity_days: int = 7
    ) -> str:
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/presigned_url/{filename}"
        )
        response = requests.get(url, params={"validityDays": validity_days})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def getPdfPagePicture(
        self, apporuser: str, project: str, pdffilename: str, page: int
    ):
        assert pdffilename.endswith(".pdf")
        justfilename = pdffilename[:-4]
        if "/" in justfilename:
            justfilename = justfilename.split("/")[-1]
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/presigned_url/{justfilename}/{page}.png"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def getCoverForBook(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/presigned_url/{filename + '.png'}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def deleteProjectFromBackend(self, apporuser: str, project: str):
        url = self.vectoratorurl + f"/{self.mainappname + '_' + apporuser}/{project}/"
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def quicksearch(self, apporuser: str, project: str, query: str) -> ChatMessage:
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/quicksearch/{query}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatMessage(**response.json())

    # Document operations
    def getDocuments(self, apporuser: str, project: str) -> List[FullDocument]:
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/documents"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [FullDocument(**doc) for doc in response.json()]

    def getDocumentById(self, apporuser: str, project: str, document_id: int):
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/documents/{document_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def deleteDocumentById(self, apporuser: str, project: str, document_id: int):
        url = (
            self.vectoratorurl
            + f"/{self.mainappname + '_' + apporuser}/{project}/documents/{document_id}"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    ### Chat routes
    def getChats(self, apporuser: str, project: str) -> List[ChatWithMessagesPD]:
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [ChatWithMessagesPD(**chat) for chat in response.json()]

    def getChat(self, apporuser: str, project: str, chat_id: int) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/{chat_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def getChatStatus(
        self, apporuser: str, project: str, chat_id: int
    ) -> ProcessingState:
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/status/{chat_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ProcessingState(response.json())

    def createChat(
        self, apporuser: str, project: str, chat: NewChatPD
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/"
        )
        if self.mainappname not in chat.apporuser:
            chat.apporuser = self.mainappname + "_" + chat.apporuser
        response = requests.post(url, json=json.loads(chat.model_dump_json()))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def addMessage(
        self, apporuser: str, project: str, message: ChatMessage
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/message"
        )
        response = requests.put(url, json=json.loads(message.model_dump_json()))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def deleteChat(self, apporuser: str, project: str, chat_id: int):
        url = (
            self.vectoratorurl
            + f"/chat/{self.mainappname + '_' + apporuser}/{project}/{chat_id}"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def simpleQuestion(
        self,
        apporuser: str,
        project: str,
        question: str,
    ) -> int:
        # returns chat id which can be used to query getChat until result
        new_chat = NewChatPD(
            name="new chat " + date.today().isoformat(),
            apporuser=apporuser,
            project=project,
            messages=[ChatMessage(message=question, persona=Persona.user)],
        )

        chat = self.createChat(apporuser, project, new_chat)
        return chat.id

    # simplified question route
    def questionWaitUntilFinished(
        self, apporuser: str, project: str, question: str, chat_id: int = None
    ) -> ChatWithMessagesPD:
        if chat_id is not None:
            message = ChatMessage(
                chat_id=chat_id, message=question, persona=Persona.user
            )
            chat = self.addMessage(apporuser, project, message)
        else:
            new_chat = NewChatPD(
                name="new chat " + date.today().isoformat(),
                apporuser=apporuser,
                project=project,
                messages=[ChatMessage(message=question, persona=Persona.user)],
            )
            chat = self.createChat(apporuser, project, new_chat)

        maxtries = 30
        crntTry = 0
        while chat.processing_state != ProcessingState.DONE and crntTry < maxtries:
            # Use the new getChatStatus endpoint for efficiency
            status = self.getChatStatus(apporuser, project, chat.id)
            if status == ProcessingState.DONE:
                break
            crntTry += 1

        # Fetch the full chat once the status is DONE or we've reached max tries
        chat = self.getChat(apporuser, project, chat.id)

        if chat.processing_state != ProcessingState.DONE:
            raise HTTPException(
                status_code=408, detail="Request timeout while processing chat"
            )

        return chat
