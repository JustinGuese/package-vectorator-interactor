import json
from datetime import date
from typing import List

import requests
from fastapi import HTTPException, UploadFile

from vectoratorinteractor.models import (
    ChatMessage,
    ChatWithMessagesPD,
    DocumentUploadRequest,
    DocumentUploadRequestWithDocumentsPD,
    FullDocument,
    NewChatPD,
    NewMessagePD,
    Persona,
    ProcessingState,
    Project,
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

    def __getOrRaiseApporuserConstructor(self, apporuser: str):
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

    def uploadDocuments(
        self,
        project: str,
        files: List[UploadFile],
        apporuser: str = "",
        highresmode: bool = False,
    ) -> DocumentUploadRequest:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/upload/"
        )
        newFiles = []
        for f in files:
            newFiles.append(("upload_files", (f.filename, f.file, f.content_type)))

        response = requests.post(
            url, files=newFiles, params={"highresmode": highresmode}
        )
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return DocumentUploadRequest(**response.json())

    def getUploadRequests(
        self, project: str, apporuser: str = ""
    ) -> List[DocumentUploadRequestWithDocumentsPD]:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/uploadrequests"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [DocumentUploadRequestWithDocumentsPD(**req) for req in response.json()]

    def getUploadRequestById(
        self, project: str, uploadrequest_id: int, apporuser: str = ""
    ) -> DocumentUploadRequestWithDocumentsPD:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/uploadrequests/{uploadrequest_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return DocumentUploadRequestWithDocumentsPD(**response.json())

    def getProjects(self, apporuser: str) -> List[str]:
        url = (
            self.vectoratorurl
            + f"/projects/{self.__getOrRaiseApporuserConstructor(apporuser)}/"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def createProject(self, project: str, apporuser: str = "") -> Project:
        url = (
            self.vectoratorurl
            + f"/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/"
        )
        response = requests.post(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return Project(**response.json())

    def listFiles(self, project: str, apporuser: str = "") -> List[str]:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/s3files"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def getPresignedUrl(
        self, project: str, filename: str, apporuser: str = "", validity_days: int = 7
    ) -> str:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/presigned_url/{filename}"
        )
        response = requests.get(url, params={"validityDays": validity_days})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def getPdfPagePicture(
        self, project: str, pdffilename: str, page: int, apporuser: str = ""
    ):
        assert pdffilename.endswith(".pdf")
        justfilename = pdffilename[:-4]
        if "/" in justfilename:
            justfilename = justfilename.split("/")[-1]
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/presigned_url/{justfilename}/{page}.png"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def getCoverForBook(self, project: str, filename: str, apporuser: str = "") -> str:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/presigned_url/{filename + '.png'}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.text.replace('"', "")

    def deleteProjectFromBackend(self, project: str, apporuser: str = ""):
        url = (
            self.vectoratorurl
            + f"/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    def quicksearch(
        self, project: str, query: str, apporuser: str = ""
    ) -> List[QuickSearchDocument]:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/quicksearch/{query}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [QuickSearchDocument(**doc) for doc in response.json()]

    # Document operations
    def getDocuments(self, project: str, apporuser: str = "") -> List[FullDocument]:
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [FullDocument(**doc) for doc in response.json()]

    def getDocumentById(self, project: str, document_id: int, apporuser: str = ""):
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{document_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()

    def deleteDocumentById(self, project: str, document_id: int, apporuser: str = ""):
        url = (
            self.vectoratorurl
            + f"/documents/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{document_id}"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    ### Chat routes
    def getChats(self, project: str, apporuser: str = "") -> List[ChatWithMessagesPD]:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return [ChatWithMessagesPD(**chat) for chat in response.json()]

    def getChat(
        self, project: str, chat_id: int, apporuser: str = ""
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{chat_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def getChatByName(
        self, project: str, chatname: str, apporuser: str = ""
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/by_name/{chatname}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def getChatStatus(
        self, project: str, chat_id: int, apporuser: str = ""
    ) -> ProcessingState:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/status/{chat_id}"
        )
        response = requests.get(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ProcessingState(response.json())

    def createChat(
        self, project: str, chatname: str, apporuser: str = ""
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{chatname}"
        )

        response = requests.post(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def renameChat(
        self, project: str, chat_id: int, new_name: str, apporuser: str = ""
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{chat_id}/rename"
        )
        response = requests.put(url, params={"new_name": new_name})
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def addMessage(
        self, project: str, chat_id: int, message: NewMessagePD, apporuser: str = ""
    ) -> ChatWithMessagesPD:
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{chat_id}/message"
        )
        response = requests.put(url, json=json.loads(message.model_dump_json()))
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return ChatWithMessagesPD(**response.json())

    def deleteChat(self, project: str, chat_id: int, apporuser: str = ""):
        url = (
            self.vectoratorurl
            + f"/chat/{self.__getOrRaiseApporuserConstructor(apporuser)}/{project}/{chat_id}"
        )
        response = requests.delete(url)
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)

    # def simpleQuestion(
    #     self,
    #     apporuser: str,
    #     project: str,
    #     question: str,
    # ) -> int:
    #     # returns chat id which can be used to query getChat until result
    #     new_chat = NewChatPD(
    #         name="new chat " + date.today().isoformat(),
    #         apporuser=apporuser,
    #         project=project,
    #         messages=[ChatMessage(message=question, persona=Persona.user)],
    #     )

    #     chat = self.createChat(apporuser, project, new_chat)
    #     return chat.id

    # simplified question route
    def questionWaitUntilFinished(
        self, project: str, question: str, apporuser: str = "", chat_id: int = None
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

    def stream_answer(self, apporuser: str, project: str, messages: list[ChatMessage]):
        url = self.vectoratorurl + f"/stream/{apporuser}/{project}/"
        response = requests.post(
            url,
            json={"messages": [json.loads(m.model_dump_json()) for m in messages]},
            stream=True,
        )
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.iter_content(chunk_size=None)

    def stream_answer_tokens(
        self, apporuser: str, project: str, messages: list[ChatMessage]
    ):
        url = self.vectoratorurl + f"/stream/{apporuser}/{project}/tokens"
        response = requests.post(
            url,
            json={"messages": [json.loads(m.model_dump_json()) for m in messages]},
            stream=True,
        )
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.iter_content(chunk_size=None)

    def stream_answer_events(
        self, apporuser: str, project: str, messages: list[ChatMessage]
    ):
        url = self.vectoratorurl + f"/stream/{apporuser}/{project}/events"
        response = requests.post(
            url,
            json={"messages": [json.loads(m.model_dump_json()) for m in messages]},
            stream=True,
        )
        if not response.ok:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.iter_content(chunk_size=None)
