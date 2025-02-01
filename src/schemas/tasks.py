from pydantic import BaseModel


class ParseTasksResponse(BaseModel):
    status: int
    details: str
    data: list
