import json
from datetime import date
from typing import List

import requests
from fastapi import HTTPException, UploadFile

from vectoratorinteractor.models import (
    ChatMessage,
    ChatWithMessagesPD,
    DocumentUploadRequest,
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
            + f"/upload/{self.mainappname + '_' + apporuser}/{project}"
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
            + f"/uploadrequests/{self.mainappname + '_' + apporuser}/{project}"
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
        url = (
            self.vectoratorurl
            + f"/projects/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.post(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return Project(**response.json())

    def listFiles(self, apporuser: str, project: str) -> List[str]:
        url = (
            self.vectoratorurl
            + f"/files/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def getPresignedUrl(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/presigned_url/{self.mainappname + '_' + apporuser}/{project}/{filename}"
        )
        response = requests.get(url)
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
            + f"/presigned_url/{self.mainappname + '_' + apporuser}/{project}/{justfilename}/{page}.png"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def getCoverForBook(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/presigned_url/{self.mainappname + '_' + apporuser}/{project}/{filename + '.png'}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def deleteProjectFromBackend(self, apporuser: str, project: str):
        url = self.vectoratorurl + f"/{self.mainappname + '_' + apporuser}/{project}"
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def quicksearch(self, apporuser: str, project: str, query: str) -> ChatMessage:
        url = (
            self.vectoratorurl
            + f"/quicksearch/{self.mainappname + '_' + apporuser}/{project}/{query}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatMessage(**response.json())

    ### Chat routes
    def getChats(self, apporuser: str, project: str) -> List[ChatWithMessagesPD]:
        url = (
            self.vectoratorurl + f"/chat/{self.mainappname + '_' + apporuser}/{project}"
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

    def createChat(self, chat: NewChatPD) -> ChatWithMessagesPD:
        url = self.vectoratorurl + "/chat/"
        response = requests.post(url, json=json.loads(chat.model_dump_json()))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def addMessage(
        self, apporuser: str, project: str, message: ChatMessage
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/message/{self.mainappname + '_' + apporuser}/{project}"
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
            apporuser=self.mainappname + "_" + apporuser,
            project=project,
            messages=[ChatMessage(message=question, persona=Persona.user)],
        )

        chat = self.createChat(new_chat)
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
                apporuser=self.mainappname + "_" + apporuser,
                project=project,
                messages=[ChatMessage(message=question, persona=Persona.user)],
            )
            chat = self.createChat(new_chat)

        maxtries = 30
        crntTry = 0
        while chat.processing_state != ProcessingState.DONE and crntTry < maxtries:
            chat = self.getChat(apporuser, project, chat.id)
            crntTry += 1

        if chat.processing_state != ProcessingState.DONE:
            raise HTTPException(
                status_code=408, detail="Request timeout while processing chat"
            )

        return chat
