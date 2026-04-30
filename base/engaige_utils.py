import os
from dotenv import load_dotenv
from base.requests_utils import get_with_retry
from base.logger import logger
from time import sleep


def get_all_messages():
    load_dotenv()
    engaige_token = os.getenv("ENGAIGE_TOKEN")

    data = []

    max_iters_safety = 200
    response0 = get_with_retry("https://autoresponder.ai.salesupply.com/messages", headers={"Authorization": engaige_token})
    data.extend(response0.json()['data'])
    next_url = response0.json()['next_page_url']
    for it in range(max_iters_safety):
        response = get_with_retry(next_url, headers={"Authorization": engaige_token})
        data.extend(response.json()['data'])
        next_url = response.json()['next_page_url']
        sleep(1)
        if not next_url:
            break
        if it > max_iters_safety:
            logger.warning(f"Max iterations reached: {max_iters_safety}")
            break
    return data