from enum import IntEnum
from pydantic import BaseModel
from datetime import datetime
from bs4 import BeautifulSoup



class MailboxId(IntEnum):
    unhandled = 1
    handled = 2
    sent = 3
    unknown4 = 4
    draft = 6
    unknown = 5
    unknown7 = 7
    unknown8 = 8
    unknown9 = 9


class MessageCategory(BaseModel):
    Id: int
    Name: str
    ParentMessageCategoryId: int | None = None
    ShopId: int | None = None
    ShopOwnerId: int | None = None
    ParentMessageCategories: list["MessageCategory"] | None = []


class Email(BaseModel):
    MailServerMsgId: str
    FromAddress: str
    ToAddress: str
    CcAddress: str
    BccAddress: str
    Subject: str
    Content: str
    Note: str
    Categories: list[MessageCategory]
    EmployeeId: int | None = None
    OrderId: int | None = None
    ReplyOnMailId: int | None = None
    Id: int
    ShopId: int
    Date: datetime
    MailboxId: MailboxId

    def content_as_text(self) -> str:
        soup = BeautifulSoup(self.Content, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        clean_text = "\n".join(line for line in lines if line)
        return clean_text

EmailMessage = Email # Legacy model


class MailTemplateType(IntEnum):
    ForCustomer = 1
    ForSupplier = 2


class MailKind(IntEnum):
    General = 0
    Unknown_1 = 1
    Order = 2
    Unknown_3 = 3
    Unknown_4 = 4
    Unknown_5 = 5
    Unknown_6 = 6
    Unknown_7 = 7
    Unknown_8 = 8
    Unknown_9 = 9
    Unknown_10 = 10
    Unknown_11 = 11
    Unknown_12 = 12
    Unknown_13 = 13
    Unknown_14 = 14
    Unknown_15 = 15
    Unknown_16 = 16
    Unknown_17 = 17
    Unknown_18 = 18
    Unknown_19 = 19
    Unknown_20 = 20
    Unknown_21 = 21
    Unknown_22 = 22
    Unknown_23 = 23
    Unknown_24 = 24
    Unknown_25 = 25
    Unknown_26 = 26
    Unknown_27 = 27
    Unknown_28 = 28
    Unknown_29 = 29
    Unknown_30 = 30
    Unknown_31 = 31
    Unknown_32 = 32
    Unknown_33 = 33
    Unknown_34 = 34
    Unknown_35 = 35
    Unknown_36 = 36
    Unknown_37 = 37
    Unknown_38 = 38
    Unknown_39 = 39
    Unknown_40 = 40
    Unknown_41 = 41
    Unknown_42 = 42
    Unknown_43 = 43
    Unknown_44 = 44
    Unknown_45 = 45
    Unknown_46 = 46
    Unknown_47 = 47
    Unknown_48 = 48
    Unknown_49 = 49
    Unknown_50 = 50
    Unknown_51 = 51
    Unknown_52 = 52
    Unknown_53 = 53
    Unknown_54 = 54
    Unknown_55 = 55
    Unknown_56 = 56
    Unknown_57 = 57
    Unknown_58 = 58
    Unknown_59 = 59
    Supplier = 60


class MailTemplateListItem(BaseModel):
    Id: int
    Name: str


class MailTemplate(BaseModel):
    Id: int
    Name: str
    ShopId: int
    ShopOwnerId: int
    CultureId: int | None = None
    CultureCode: str
    Code: str
    Subject: str
    Content: str
    ToAddress: str
    CcAddress: str
    BccAddress: str
    Comment: str
    TemplateType: MailTemplateType
    MailKind: MailKind
    Publish: bool

    def content_as_text(self) -> str:
        soup = BeautifulSoup(self.Content, "html.parser")
        text = soup.get_text(separator="\n")
        lines = [line.strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)