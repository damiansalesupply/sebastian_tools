from enum import Enum

from .models.tickets import MailMessage, VoipMessage, ChatMessage, TicketMessageType, Ticket, OrderComment, TicketWithEmails
from .requests_utils import get_with_retry
from .logger import logger
from dotenv import load_dotenv
import os
from .models.emails import MailboxId, Email, MailTemplate, MailTemplateListItem
import time

class ShopCtrlInstance(Enum):
    Cms = "cms"
    Expert = "expert"

BASE_URL = {
    ShopCtrlInstance.Cms: "https://api.salesupply.com/v1",
    ShopCtrlInstance.Expert: "https://expert.salesupply.com:52222/v1",
}

def get_auth_header(shopctrl_instance: ShopCtrlInstance) -> str:
    return os.getenv("SHOPCTRL_BASIC_AUTH_HEADER") if shopctrl_instance == ShopCtrlInstance.Cms else os.getenv("SHOPCTRL_EXPERT_BASIC_AUTH_HEADER")


def get_list_of_shops(shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms) -> list:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }
    endpoint = f"{BASE_URL[shopctrl_instance]}/Shops"
    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return [shop for shop in response.json()]

################################################
# MAIL TEMPLATES
################################################

def get_list_of_templates(shop_id: int | str, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms) -> list[MailTemplateListItem]:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }
    endpoint = f"{BASE_URL[shopctrl_instance]}/Shops/{shop_id}/EmailTemplates"
    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return [MailTemplateListItem(**item) for item in response.json()]


def get_template_details(template_id: int | str, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms) -> MailTemplate:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }
    endpoint = f"{BASE_URL[shopctrl_instance]}/MailTemplates/{template_id}"
    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return MailTemplate(**response.json())


def get_list_of_templates_details(shop_id: int | str, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms) -> list[MailTemplate]:
    templates = get_list_of_templates(shop_id, shopctrl_instance)
    return [get_template_details(t.Id, shopctrl_instance) for t in templates]


################################################
# EMAILS
################################################

def get_list_of_emails_ids(
    shop_id: int|str,
    from_date: str | None = None,
    until_date: str | None = None,
    mailbox_id: MailboxId | None = None,
    delay: float = 0.0,
    debug: bool = False,
    max_results: int = 1000,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
) -> list[str|int]:

    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Shops/{shop_id}/Emails"

    email_ids = []
    max_pages = 1_000
    for page_number in range(1, max_pages):
        params = {
            "fromDate": from_date,
            "untilDate": until_date,
            "mailboxId": None if mailbox_id is None else mailbox_id.value,
            "pageSize": 1_000,
            "pageNumber": page_number,
        }

        if debug:
            print(f"Page {page_number} of {max_pages} - {len(email_ids)} emails")
            # print(params)

        response = get_with_retry(endpoint, headers=headers, params=params, timeout0=15 if page_number == 1 else 5)
        response.raise_for_status()
        emails = response.json()
        email_ids.extend([email['Id'] for email in emails])
        if not len(emails):
            break
        if len(email_ids) >= max_results:
            break
        time.sleep(delay)
    return email_ids


def get_email_details(email_id: str|int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms) -> Email:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Emails/{email_id}"

    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return Email(**response.json())


def get_email_thread_details(email_id: str|int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms) -> list[Email]:
    email_details = get_email_details(email_id, shopctrl_instance)
    thread = [email_details,]
    while email_details.ReplyOnMailId:
        email_details = get_email_details(email_id=email_details.ReplyOnMailId, shopctrl_instance=shopctrl_instance)
        thread.append(email_details)
    return thread[::-1]

################################################
# TICKETS
################################################

def get_list_of_tickets_ids(shop_id: int|str, from_date_changed: str | None = None, until_date_changed: str | None = None, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert, max_results: int = 100_000) -> list[int]:
    """untilDateChanged is exclusive on the API: use the day after your last inclusive day."""
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Shops/{shop_id}/Tickets"

    tickets_ids = []
    for page_number in range(1, 1000):
        params = {
            "fromDateChanged": from_date_changed,
            "untilDateChanged": until_date_changed,
            "pageSize": 1000,
            "pageNumber": page_number,
        }

        response = get_with_retry(endpoint, headers=headers, params=params)
        response.raise_for_status()
        tickets = response.json()
        tickets_ids.extend([ticket['Id'] for ticket in tickets])
        if not len(tickets):
            break
        if len(tickets_ids) >= max_results:
            break
    
    return tickets_ids

def get_list_of_tickets_ids_and_codes(shop_id: int|str, from_date_changed: str | None = None, until_date_changed: str | None = None, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert, max_results: int = 100_000) -> list[int]:
    """untilDateChanged is exclusive on the API: use the day after your last inclusive day."""
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Shops/{shop_id}/Tickets"

    tickets_ids_and_codes = []
    for page_number in range(1, 1000):
        params = {
            "fromDateChanged": from_date_changed,
            "untilDateChanged": until_date_changed,
            "pageSize": 1000,
            "pageNumber": page_number,
        }

        response = get_with_retry(endpoint, headers=headers, params=params)
        response.raise_for_status()
        tickets = response.json()
        tickets_ids_and_codes.extend([(ticket['Id'], ticket['TicketCode']) for ticket in tickets])
        if not len(tickets):
            break
        if len(tickets_ids_and_codes) >= max_results:
            break
    
    return tickets_ids_and_codes

def get_ticket_details(ticket_id: int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert) -> Ticket:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Tickets/{ticket_id}"

    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return Ticket(**response.json())

def get_ticket_messages(ticket_id: int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert, *, include_mail: bool = True, include_voip: bool = True, include_chat: bool = True) -> list[MailMessage | VoipMessage | ChatMessage]:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Tickets/{ticket_id}/Messages"

    params = {
        "includeMail": include_mail,
        "includeVoip": include_voip,
        "includeChat": include_chat,
    }

    response = get_with_retry(endpoint, headers=headers, params=params)
    response.raise_for_status()

    def create_ticket_message(message) -> MailMessage | VoipMessage | ChatMessage:
        if message['Type'] == TicketMessageType.Mail:
            return MailMessage(**message)
        elif message['Type'] == TicketMessageType.Voip:
            return VoipMessage(**message)
        elif message['Type'] == TicketMessageType.Chat:
            raise NotImplementedError("Chat messages are not supported yet")
            # return ChatMessage(**message)
        else:
            raise ValueError(f"Unknown ticket message type: {message['Type']}")

    return [create_ticket_message(message) for message in response.json()]

def get_ticket_comments(ticket_id: int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert) -> list[OrderComment]:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json"
    }
    endpoint = f"{BASE_URL[shopctrl_instance]}/Tickets/{ticket_id}/Comments"
    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return [OrderComment(**comment) for comment in response.json()]

def get_ticket_emails(ticket_id: int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert) -> list[Email]:
    messages: list[MailMessage] = get_ticket_messages(ticket_id, shopctrl_instance=shopctrl_instance, include_mail=True, include_chat=False, include_voip=False)
    return [get_email_details(message.Id, shopctrl_instance=shopctrl_instance) for message in messages]

def get_ticket_with_emails(ticket_id: int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert) -> TicketWithEmails:
    ticket = get_ticket_details(ticket_id, shopctrl_instance=shopctrl_instance)
    emails = get_ticket_emails(ticket_id, shopctrl_instance=shopctrl_instance)
    return TicketWithEmails(**ticket.model_dump(), Emails=emails)

# def get_ticket_messages_as_text(ticket_id: int, shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Expert, include_mail: bool = True, include_chat: bool = True) -> list[str]:
    # messages = get_ticket_messages(ticket_id, shopctrl_instance, include_mail=include_mail, include_chat=include_chat)
