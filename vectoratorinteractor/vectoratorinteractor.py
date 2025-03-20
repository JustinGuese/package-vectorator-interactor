import json
from datetime import date
from typing import List

import requests
from fastapi import UploadFile

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
        response.raise_for_status()

    def getUploadRequests(
        self, apporuser: str, project: str
    ) -> List[DocumentUploadRequest]:
        url = (
            self.vectoratorurl
            + f"/uploadrequests/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return [DocumentUploadRequest(**req) for req in response.json()]

    def getProjects(self, apporuser: str) -> List[str]:
        url = self.vectoratorurl + f"/projects/{self.mainappname + '_' + apporuser}/"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def createProject(self, apporuser: str, project: str) -> Project:
        url = (
            self.vectoratorurl
            + f"/projects/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.post(url)
        response.raise_for_status()
        return Project(**response.json())

    def listFiles(self, apporuser: str, project: str) -> List[str]:
        url = (
            self.vectoratorurl
            + f"/files/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def getPresignedUrl(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/presigned_url/{self.mainappname + '_' + apporuser}/{project}/{filename}"
        )
        response = requests.get(url)
        response.raise_for_status()
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
        response.raise_for_status()
        return response.text.replace('"', "")

    def getCoverForBook(self, apporuser: str, project: str, filename: str) -> str:
        url = (
            self.vectoratorurl
            + f"/presigned_url/{self.mainappname + '_' + apporuser}/{project}/{filename + '.png'}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return response.text.replace('"', "")

    def deleteProjectFromBackend(self, apporuser: str, project: str):
        url = self.vectoratorurl + f"/{self.mainappname + '_' + apporuser}/{project}"
        response = requests.delete(url)
        response.raise_for_status()

    def quicksearch(self, apporuser: str, project: str, query: str) -> ChatMessage:
        url = (
            self.vectoratorurl
            + f"/quicksearch/{self.mainappname + '_' + apporuser}/{project}/{query}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return ChatMessage(**response.json())

    ### Chat routes
    def getChats(self, apporuser: str, project: str) -> List[ChatWithMessagesPD]:
        url = (
            self.vectoratorurl + f"/chat/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return [ChatWithMessagesPD(**chat) for chat in response.json()]

    def getChat(self, chat_id: int) -> ChatWithMessagesPD:
        url = self.vectoratorurl + f"/chat/{chat_id}"
        response = requests.get(url)
        response.raise_for_status()
        return ChatWithMessagesPD(**response.json())

    def createChat(self, chat: NewChatPD) -> ChatWithMessagesPD:
        url = self.vectoratorurl + "/chat/"
        response = requests.post(url, json=json.loads(chat.model_dump_json()))
        response.raise_for_status()
        return ChatWithMessagesPD(**response.json())

    def addMessage(
        self, apporuser: str, project: str, message: ChatMessage
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/message/{self.mainappname + '_' + apporuser}/{project}"
        )
        response = requests.put(url, json=message.model_dump_json())
        response.raise_for_status()
        return ChatWithMessagesPD(**response.json())

    def deleteChat(self, chat_id: int):
        url = self.vectoratorurl + f"/chat/{chat_id}"
        response = requests.delete(url)
        response.raise_for_status()

    def simpleQuestion(
        self,
        apporuser,
        project,
        question,
    ) -> int:
        # returns chat id which can be used to query getChat until result
        NewChatPD = NewChatPD(
            name="new chat" + date.today().isoformat(),
            apporuser=self.mainappname + "_" + apporuser,
            project=project,
            messages=[{"message": question, "persona": "user"}],
        )

        chat = self.createChat(NewChatPD)
        return chat.id

    # simplified question route
    def questionWaitUntilFinished(
        self, apporuser: str, project: str, question: str, chat_id: int = None
    ) -> ChatWithMessagesPD:
        if chat_id is not None:
            self.addMessage(
                apporuser,
                project,
                ChatMessage(chat_id=chat_id, message=question, persona=Persona.user),
            )
            chat = self.getChat(chat_id)
        else:
            NewChatPD = NewChatPD(
                name="new chat" + date.today().isoformat(),
                apporuser=self.mainappname + "_" + apporuser,
                project=project,
                messages=[{"message": question, "persona": "user"}],
            )
            chat = self.createChat(NewChatPD)
        maxtries = 30
        crntTry = 0
        while chat.processing_state != ProcessingState.DONE and crntTry < maxtries:
            chat = self.getChat(chat.id)
            crntTry += 1
        assert chat.processing_state == ProcessingState.DONE
        return chat
