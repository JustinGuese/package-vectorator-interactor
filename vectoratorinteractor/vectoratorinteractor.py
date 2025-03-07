from datetime import datetime
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

class ChatResponse(BaseModel):
    question: str
    chat_history: List[Message]
    answer: str
    source_documents: List[SourceDocumentPD]

class VectoratorInteractor:
    def __init__(self, mainappname: str, vectoratorurl: str = "http://vectorator-service.vectorator.svc.cluster.local:8000"):
        self.mainappname = mainappname
        self.vectoratorurl = vectoratorurl

    def uploadDocuments(self, apporuser: str, project: str, files: List[UploadFile], highresmode: bool = False):
        url = self.vectoratorurl + f"/upload/{self.mainappname + "_" + apporuser}/{project}"
        newFiles = []
        for f in files:
            newFiles.append(('upload_files', (f.filename, f.file, f.content_type)))

        response = requests.post(url,  files=newFiles, params={"highresmode": highresmode})
        response.raise_for_status()

        
    def getPresignedUrl(self, apporuser: str, project: str, filename: str) -> str:
        url = self.vectoratorurl + f"/presigned_url/{self.mainappname + "_" + apporuser}/{project}/{filename}"
        response = requests.get(url)
        response.raise_for_status()
        return response.text.replace('"', "")
    
    def getCoverForBook(self, apporuser: str, project: str, filename: str) -> str:
        url = self.vectoratorurl + f"/presigned_url/{self.mainappname + "_" + apporuser}/{project}/{filename + '.png'}"
        response = requests.get(url, params={"validityDays": 365})
        response.raise_for_status()
        return response.text.replace('"', "")

    def question(self, question, apporuser, project_name, messages: dict) -> ChatResponse:
        url = self.vectoratorurl + f"/question/{self.mainappname + "_" + apporuser}/{project_name}"
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
        return ChatResponse(**response.json())


    def deleteProjectFromBackend(self, apporuser: str, project: str):
        url = self.vectoratorurl + f"/{self.mainappname + "_" + apporuser}/{project}"
        response = requests.delete(url)
        response.raise_for_status()

    def quicksearch(self, apporuser: str, project: str, query: str) -> ChatResponse:
        url = self.vectoratorurl + f"/quicksearch/{self.mainappname + "_" + apporuser}/{project}/{query}"
        response = requests.get(url)
        response.raise_for_status()
        return ChatResponse(**response.json())