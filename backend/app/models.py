import uuid
from datetime import datetime
from sqlite3 import Time

from pydantic import EmailStr
from sqlalchemy import Date
from sqlmodel import Field, Relationship, SQLModel
from pydantic import BaseModel

STATUS_COMPLETE = 1
STATUS_PENDING = 0

DOCUMENT_W2 = "W-2"
DOCUMENT_F1090 = "F-1090"


# Shared properties
class UserBase(SQLModel):
    email: EmailStr = Field(unique=True, index=True, max_length=255)
    is_active: bool = True
    is_superuser: bool = False
    full_name: str | None = Field(default=None, max_length=255)
    recipient_name: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    state: str | None = Field(default=None, max_length=255)
    zipcode: str | None = Field(default=None, max_length=255)
    ssn: str | None = Field(default=None, max_length=255)

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=40)


class UserRegister(SQLModel):
    email: EmailStr = Field(max_length=255)
    password: str = Field(min_length=8, max_length=40)
    full_name: str = Field(max_length=255)


# Properties to receive via API on update, all are optional
class UserUpdate(UserBase):
    email: EmailStr | None = Field(default=None, max_length=255)  # type: ignore
    password: str | None = Field(default=None, min_length=8, max_length=40)


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)
    recipient_name: str | None = Field(default=None, max_length=255)
    street: str | None = Field(default=None, max_length=255)
    city: str | None = Field(default=None, max_length=255)
    state: str | None = Field(default=None, max_length=255)
    zipcode: str | None = Field(default=None, max_length=255)
    ssn: str | None = Field(default=None, max_length=255)


class UpdatePassword(SQLModel):
    current_password: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=40)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    hashed_password: str
    items: list["Item"] = Relationship(back_populates="owner", cascade_delete=True)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ItemBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on item creation
class ItemCreate(ItemBase):
    pass


# Properties to receive on item update
class ItemUpdate(ItemBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Item(ItemBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    title: str = Field(max_length=255)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="items")


# Properties to return via API, id is always required
class ItemPublic(ItemBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ItemsPublic(SQLModel):
    data: list[ItemPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"
    email: str = ""


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


class NewPassword(SQLModel):
    token: str
    new_password: str = Field(min_length=8, max_length=40)


class W2FormModel(SQLModel):
    employee_ssn: str = Field(default="", max_length=255)
    employer_ein: str = Field(default="", max_length=255)
    employer_name_address_zip: str = Field(default="", max_length=255)
    control_number: str = Field(default="", max_length=255)
    employee_first_name_initial: str = Field(default="", max_length=255)
    employee_address_zip: str = Field(default="", max_length=255)
    wages_tips_other_compensation: str = Field(default="", max_length=255)
    federal_income_tax_withheld: str = Field(default="", max_length=255)
    social_security_wages: str = Field(default="", max_length=255)
    social_security_tax_withheld: str = Field(default="", max_length=255)
    medicare_wages_tips: str = Field(default="", max_length=255)
    medicare_tax_withheld: str = Field(default="", max_length=255)
    social_security_tips: str = Field(default="", max_length=255)
    allocated_tips: str = Field(default="", max_length=255)
    dependent_care_benefits: str = Field(default="", max_length=255)
    nonqualified_plans: str = Field(default="", max_length=255)
    box_12a: str = Field(default="", max_length=255)
    box_12b: str = Field(default="", max_length=255)
    box_12c: str = Field(default="", max_length=255)
    box_12d: str = Field(default="", max_length=255)
    other: str = Field(default="", max_length=255)
    state_employer_state_id: str = Field(default="", max_length=255)
    state_wages_tips: str = Field(default="", max_length=255)
    state_income_tax: str = Field(default="", max_length=255)
    local_wages_tips: str = Field(default="", max_length=255)
    local_income_tax: str = Field(default="", max_length=255)
    locality_name: str = Field(default="", max_length=255)

class TaxDocumentResponse(BaseModel):
    message: str
    keyword: str
    value: str
    options: list[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str
    isFirst: bool

class VerifyCodeRequest(BaseModel):
    email: str
    verification_code: str
#
# # History Model
# class HistoryBase(SQLModel):
#     date: Date = Field(default=None, max_length=255)
#     time: Time = Field(default=None, max_length=255)
#     document_name: str = Field(default=None, max_length=255)
#     status: int = Field(default=STATUS_PENDING, max_length=10)
#     owner: str = Field(default=None, max_length=255)
#     size: int = Field(default=0, max_length=255)
#     file_type: str = Field(default=None, max_length=10)
#     document_type: str = Field(default=None, max_length=10)
#
# class HistoryCreate(HistoryBase):
#     pass
#
# class History(HistoryBase, table=True):
#     id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
#     owner_id: uuid.UUID = Field(
#         foreign_key="user.id", nullable=False, ondelete="CASCADE"
#     )
#     owner: "User" = Relationship(back_populates="history")
#
# class HistoryPublic(HistoryBase):
#     id: uuid.UUID
#     owner_id: uuid.UUID
#
# class HistorysPublic(SQLModel):
#     data: list[HistoryPublic]
#     count: int
#
# class HistoryUpdate(HistoryBase):
#     id: uuid.UUID


# Database model for Submissions
class SubmissionBase(SQLModel):
    date: datetime
    time: str
    document: str = Field(max_length=255)
    status: str = Field(max_length=50)  # e.g., "Completed", "Pending"
    owner: str = Field(max_length=255)  # e.g., "User_123"
    size: str = Field(max_length=50)  # e.g., "4.5MB"
    type: str = Field(max_length=10)  # e.g., "PDF", "DOCX", "XLS"
    priority: str = Field(max_length=10)  # e.g., "High", "Medium", "Low"

class SubmissionCreate(SubmissionBase):
    pass


class SubmissionUpdate(SubmissionBase):
    date: datetime | None = None
    time: str | None = None
    document: str | None = None
    status: str | None = None
    owner: str | None = None
    size: str | None = None
    type: str | None = None
    priority: str | None = None


class Submission(SubmissionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)


class SubmissionPublic(SubmissionBase):
    id: uuid.UUID


class SubmissionsPublic(SQLModel):
    data: list[SubmissionPublic]
    count: int

# Database model for Opinion
class OpinionBase(SQLModel):
    date: datetime
    name: str = Field(max_length=255)
    email: str = Field(max_length=255)
    message: str = Field(max_length=255)
    status: int = Field(default=0)

class OpinionCreate(OpinionBase):
    pass

class OpinionUpdate(OpinionBase):
    date: datetime | None = None
    name: str | None = None
    email: str | None = None
    message: str | None = None
    status: int | None = None

class Opinion(OpinionBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

class OpinionPublic(OpinionBase):
    id: uuid.UUID

class OpinionsPublic(SQLModel):
    data: list[OpinionPublic]
    count: int