from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime, timedelta, date
import re
from typing import Optional

# Pydantic Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr  # Validates email format
    password: str
    ContactNumber: str = Field(..., min_length=10, max_length=15, pattern=r"^\+?\d{10,15}$")  # Allows +country_code
    DOB: date
    eventlocation: str
    eventdate: date
    eventname: str
    role: str

    @validator("ContactNumber")
    def validate_contact(cls, value):
        """Ensure the contact number contains only digits and optional + at the start"""
        if not re.match(r"^\+?\d{10,15}$", value):
            raise ValueError("Invalid contact number format. Use digits only, optionally prefixed with +.")
        return value

class Userupdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    ContactNumber: str = Field(None, min_length=10, max_length=15, pattern=r"^\+?\d{10,15}$")
    DOB: Optional[date] = None
    eventlocation: Optional[str] = None
    eventdate: Optional[date] = None
    eventname: Optional[str] = None
    active: Optional[bool] = None
    role: Optional[str] = None

    @validator("ContactNumber")
    def validate_contact(cls, value):
        """Ensure the contact number contains only digits and optional + at the start"""
        if not re.match(r"^\+?\d{10,15}$", value):
            raise ValueError("Invalid contact number format. Use digits only, optionally prefixed with +.")
        return value

class UserResponse(BaseModel):
    message: str
    id: int
    username: str
    email: str
    role: str

class AdminUserResponse(BaseModel):
    contactnumber: str
    username: str
    email: str
    dob: date
    role: str
    eventname: str
    eventlocation: str
    eventdate: date
    registrationtime: datetime

class UserLogin(BaseModel):
    username: str = Field(..., alias="mobilenumber")
    password: str

    class Config:
        populate_by_name = True  # Ensure alias is used when creating the model


class UserDelete(BaseModel):
    username: str = Field(..., alias="mobilenumber")
    class Config:
        populate_by_name = True  # Ensure alias is used when creating the model


class Token(BaseModel):
    access_token: str
    token_type: str


class EventCreate(BaseModel):
    userid: int
    title: str
    description: str
    location: str
    datetime_from: datetime
    datetime_to: datetime
    max_attendees: int

class EventUpdate(BaseModel):
    eventid: int
    userid: int
    title: str
    description: str
    location: str
    datetime_from: datetime
    datetime_to: datetime
    max_attendees: int


class EventResponse(BaseModel):
    message: str
    id: int
    organizer_id: int

