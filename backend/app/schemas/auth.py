from pydantic import BaseModel, EmailStr

class SignupSchema(BaseModel):
    email: EmailStr
    password: str

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
