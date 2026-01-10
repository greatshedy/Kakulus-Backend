from pydantic import BaseModel, EmailStr


class Admin(BaseModel):
    email: EmailStr
    password: str
    refresh_token: str = None




class LoginData(BaseModel):
    email: EmailStr
    password: str

class OtpVerify(BaseModel):
    id: str
    otp: str