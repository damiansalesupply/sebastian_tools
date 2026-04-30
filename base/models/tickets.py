from enum import Enum, IntEnum

from bs4 import BeautifulSoup
from pydantic import BaseModel
from datetime import datetime
from .emails import MessageCategory
from .emails import Email
from typing import Any



class TicketMessageType(IntEnum):
    Mail = 1
    Voip = 2
    Chat = 3


class TicketMessageDirection(IntEnum):
    Incoming = 1
    Outgoing = 2


class TicketMessage(BaseModel):
    Type: TicketMessageType
    Id: int
    Timestamp: datetime
    Direction: TicketMessageDirection
    Content: str | None = None
    EmployeeId: int | None = None
    From: str | None = None
    To: str | None = None


class BaseTicketMessage(BaseModel):
    """Base class for ticket message types with common fields."""
    Id: int
    Timestamp: datetime
    Direction: TicketMessageDirection
    Content: str | None = None
    EmployeeId: int | None = None
    From: str | None = None
    To: str | None = None

    def content_as_text(self) -> str:
        if self.Content is None:
            return ""
        soup = BeautifulSoup(self.Content, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        clean_text = "\n".join(line for line in lines if line)
        return clean_text

class MailMessage(BaseTicketMessage):
    Type: TicketMessageType = TicketMessageType.Mail
    MailboxId: int | None = None
    Subject: str | None = None


class VoipMessage(BaseTicketMessage):
    Type: TicketMessageType = TicketMessageType.Voip
    DurationSec: int | None = None

class ChatMessage(BaseTicketMessage):
    Type: TicketMessageType = TicketMessageType.Chat
    # def __init__(self, **data: Any):
    #     if data != []:
    #         raise NotImplementedError

class ParameterDataType(Enum):
    String = "String"
    Date = "Date"
    Boolean = "Boolean"
    Number = "Number"
    Lookup = "Lookup"
    RichText = "RichText"


class Parameter(BaseModel):
    Key: str
    Value: str
    DataType: ParameterDataType


class OrderComment(BaseModel):
    Id: int | None = None
    OrderId: int | None = None
    Comment: str
    EmployeeId: int | None = None
    EmployeeName: str | None = None
    TimeStamp: datetime | None = None
    OfferId: int | None = None
    TicketId: int | None = None
    CommentType: int | None = None


class Ticket(BaseModel):
    ShopId: int
    CustomerId: int | None = None
    CustomerCode: str | None = None
    Categories: list[MessageCategory] = []
    Params: list[Parameter] = []
    OpenEmployeeId: int | None = None
    OpenEmployeeFullName: str | None = None
    CloseEmployeeId: int | None = None
    CloseEmployeeFullName: str | None = None
    Prio: int | None = None
    HandlingEmployeeId: int | None = None
    HandlingEmployeeFullName: str | None = None
    TicketTypeId: int | None = None
    MailCount: int | None = None
    VoipCallCount: int | None = None
    ChatCount: int | None = None
    RemoveFromFollowUpDate: datetime | None = None
    HandlingEmployeeGroupId: int | None = None
    ParentTicketId: int | None = None
    OrderReturnId: int | None = None
    OrderReturnCode: str | None = None
    CreateTimestamp: datetime | None = None
    SlaEndTimestamp: datetime | None = None
    TotalOpenMinutes: int | None = None
    CloseToOpenCount: int | None = None
    Rating: int | None = None
    OrderId: int | None = None
    OrderCode: str | None = None
    OfferId: int | None = None
    OfferCode: str | None = None
    ProductId: int | None = None
    ProductCode: str | None = None
    HandlingEmployeeGroupChangedTimestamp: datetime | None = None
    FirstResponseTimestamp: datetime | None = None
    TaskCount: int | None = None
    TicketIdleMailId: int | None = None
    Id: int
    TicketCode: int
    Title: str
    OpenDate: datetime | None = None
    CloseDate: datetime | None = None
    ChangedTimestamp: datetime | None = None
    MainStatusId: int
    MainStatusName: str
    PreviousMainStatusId: int | None = None
    PreviousMainStatusName: str | None = None
    ServiceContractId: int | None = None

class TicketWithEmails(Ticket):
    Emails: list[Email] = []
