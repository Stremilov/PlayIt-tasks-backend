import enum

from fastapi import Form, UploadFile, File
from pydantic import BaseModel


class ParseTasksResponse(BaseModel):
    status: int
    details: str
    data: list


class TaskBaseResponse(BaseModel):
    status: str
    message: str


class StatusEnum(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class TaskSchema(BaseModel):
    id: int
    description: str
    photo_path: str
    value: int
    status: StatusEnum

    class Config:
        from_attributes = True
