from pydantic import BaseModel, EmailStr


class RegisterOrLoginReq(BaseModel):
    email: EmailStr
    password: str


class AccessTokenResp(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
