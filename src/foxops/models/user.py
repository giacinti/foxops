from pydantic import BaseModel, EmailStr, AnyUrl
from typing import Optional, List


class User(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    nickname: Optional[str] = None
    picture: Optional[AnyUrl] = None
    profile: Optional[AnyUrl] = None
    scopes: List[str] = []
