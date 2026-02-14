from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    voting_method: str = Field(pattern=r"^(consulate|mail)$")
    language_pref: str = Field(default="hu", pattern=r"^(hu|en)$")


class SignupResponse(BaseModel):
    status: str = "ok"
    message: str


class ContactRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    message: str = Field(min_length=1, max_length=5000)
    language_pref: str = Field(default="hu", pattern=r"^(hu|en)$")


class ContactResponse(BaseModel):
    status: str = "ok"
    message: str


class HelpRequestRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    message: str = Field(min_length=1, max_length=5000)
    voting_method: str = Field(pattern=r"^(consulate|mail)$")
    language_pref: str = Field(default="hu", pattern=r"^(hu|en)$")


class HelpRequestResponse(BaseModel):
    status: str = "ok"
    message: str


class CarpoolRequest(BaseModel):
    carpool_type: str = Field(pattern=r"^(offer|seek)$")
    name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=30)
    starting_location: str = Field(min_length=1, max_length=500)
    seats: int | None = Field(default=None, ge=1, le=10)
    voting_method: str = Field(pattern=r"^(consulate|mail)$")
    language_pref: str = Field(default="hu", pattern=r"^(hu|en)$")


class CarpoolResponse(BaseModel):
    status: str = "ok"
    message: str


class HealthResponse(BaseModel):
    status: str = "ok"
