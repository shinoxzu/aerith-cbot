from pydantic import BaseModel


class UserSupport(BaseModel):
    user_id: int
    end_timestamp: int
