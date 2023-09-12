import json

from pydantic import BaseModel, field_validator
from pydantic.types import Json


class GoogleMapsApiLog(BaseModel):
    user_id: int
    request_url: str
    status_code: str | int
    reason: str
    payload: str
    print_result: str

    @field_validator("payload", mode="before")
    @classmethod
    def json_to_str(cls, v: Json) -> str:
        return json.dumps(v)

    class Config:
        orm_mode = True


class GoogleMapsApiLogCreate(GoogleMapsApiLog):
    pass
