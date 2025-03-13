import logging
from datetime import datetime
from time import sleep
from typing import List

import requests
from fastapi import UploadFile
from pydantic import BaseModel


class Message(BaseModel):
    content: str
    is_ai: bool = True


class SourceDocumentPD(BaseModel):
    fullpath: str
    filename: str
    title: str
    summary: str
    content: str
    url: str
    url_expires_at: datetime


class ChatResponsePD(BaseModel):
    question: str
    answer: str | None = None
    source_documents: List[SourceDocumentPD] = []
    apporuser: str | None = None
    project: str | None = None
    subscription: str | None = None


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

    def __submitQuestion(
        self, question, apporuser, project_name, messages: dict
    ) -> int:
        url = (
            self.vectoratorurl
            + f"/question/{self.mainappname + "_" + apporuser}/{project_name}"
        )
        headers = {
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
        }
        data = {
            "question": question,
            "message_history": messages,
        }
        response = requests.post(url, headers=headers, data=data)
        response.raise_for_status()
        return int(response.text)

    # returns a chat_id
    def submitQuestion(self, question, apporuser, project_name, messages: dict) -> int:
        return self.__submitQuestion(question, apporuser, project_name, messages)

    def getChatResponseForId(self, chat_id: int) -> ChatResponsePD:
        url = self.vectoratorurl + f"/question/{chat_id}"
        response = requests.get(url)
        response.raise_for_status()
        response = response.json()
        return ChatResponsePD(**response)

    def getChatResponseForIdWaitForFinish(self, chat_id) -> ChatResponsePD:
        resp = self.getChatResponseForId(chat_id)
        if resp.answer is None:
            # still needs time
            logging.debug("answer is not ready yet, wait")
            sleep(2)
            return self.getChatResponseForIdWaitForFinish(chat_id)
        return resp

    def question(
        self, question, apporuser, project_name, messages: dict
    ) -> ChatResponsePD:
        chat_id = self.submitQuestion(question, apporuser, project_name, messages)
        return self.getChatResponseForId(chat_id)

    def isChatResponseReady(self, chat_id: int) -> bool:
        resp = self.__getChatResponse(chat_id)
        return resp.answer is not None

    def deleteProjectFromBackend(self, apporuser: str, project: str):
        url = self.vectoratorurl + f"/{self.mainappname + "_" + apporuser}/{project}"
        response = requests.delete(url)
        response.raise_for_status()

    def quicksearch(self, apporuser: str, project: str, query: str) -> ChatResponsePD:
        url = (
            self.vectoratorurl
            + f"/quicksearch/{self.mainappname + "_" + apporuser}/{project}/{query}"
        )
        response = requests.get(url)
        response.raise_for_status()
        return ChatResponsePD(**response.json())
