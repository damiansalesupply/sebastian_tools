import functools
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

from .models.orders import Order, OrderRow
from .models.tickets import OrderComment
from .requests_utils import get_with_retry
from .shopctrl_utils import BASE_URL, ShopCtrlInstance, get_auth_header

EXEC_TIMES: dict[str, list[float]] = defaultdict(list)


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        EXEC_TIMES[func.__name__].append(time.perf_counter() - start)
        return result
    return wrapper


@timeit
def get_list_of_orders_ids(
    shop_id: int | str,
    from_date_changed: str | None = None,
    until_date_changed: str | None = None,
    max_results: int = 100_000,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
) -> list[int]:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json",
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Shops/{shop_id}/Orders"

    order_ids: list[int] = []
    for page_number in range(1, 10_000):
        params = {
            "fromDateChanged": from_date_changed,
            "untilDateChanged": until_date_changed,
            "pageSize": 100,
            "pageNumber": page_number,
        }

        response = get_with_retry(endpoint, headers=headers, params=params)
        response.raise_for_status()
        orders = response.json()
        order_ids.extend([order["Id"] for order in orders])
        if not len(orders):
            break
        if len(order_ids) >= max_results:
            break

    return order_ids


@timeit
def get_order_details(
    order_id: int | str,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
) -> Order:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json",
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Orders/{order_id}"

    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return Order(**response.json())


@timeit
def get_order_rows(
    order_id: int | str,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
) -> list[OrderRow]:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json",
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Orders/{order_id}/Rows"

    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return [OrderRow(**row) for row in response.json()]


@timeit
def get_order_comments(
    order_id: int | str,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
) -> list[OrderComment]:
    load_dotenv()
    headers = {
        "Authorization": get_auth_header(shopctrl_instance),
        "Content-Type": "application/json",
    }

    endpoint = f"{BASE_URL[shopctrl_instance]}/Orders/{order_id}/OrderComments"

    response = get_with_retry(endpoint, headers=headers)
    response.raise_for_status()
    return [OrderComment(**comment) for comment in response.json()]


@timeit
def get_order_carrier_name(
    order_id: int | str,
    carrier_param_key: str = "carrierName",
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
) -> str | None:
    # 1305: carrierName
    # 1645: selectedShippingMethod
    order = get_order_details(order_id, shopctrl_instance=shopctrl_instance)
    for param in order.Params:
        if param.Key == carrier_param_key:
            return param.Value
    return None


@timeit
def get_available_carriers(
    shop_id: int | str,
    max_results: int = 1_000,
    from_date_changed: str | None = None,
    until_date_changed: str | None = None,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
    carrier_param_key: str = "carrierName",
) -> list[str]:
    order_ids = get_list_of_orders_ids(
        shop_id,
        from_date_changed=from_date_changed,
        until_date_changed=until_date_changed,
        max_results=max_results,
        shopctrl_instance=shopctrl_instance,
    )

    carriers: list[str | None] = []
    for order_id in order_ids:
        carrier = get_order_carrier_name(order_id, carrier_param_key=carrier_param_key, shopctrl_instance=shopctrl_instance)
        carriers.append(carrier)

    return carriers


@timeit
def get_available_carriers_parallel(
    shop_id: int | str,
    max_results: int = 1_000,
    from_date_changed: str | None = None,
    until_date_changed: str | None = None,
    shopctrl_instance: ShopCtrlInstance = ShopCtrlInstance.Cms,
    max_workers: int = 10,
    carrier_param_key: str = "carrierName",
) -> list[str | None]:
    order_ids = get_list_of_orders_ids(
        shop_id,
        from_date_changed=from_date_changed,
        until_date_changed=until_date_changed,
        max_results=max_results,
        shopctrl_instance=shopctrl_instance,
    )

    carriers: list[str | None] = [None] * len(order_ids)
    index_map = {oid: i for i, oid in enumerate(order_ids)}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(get_order_carrier_name, oid, carrier_param_key=carrier_param_key, shopctrl_instance=shopctrl_instance): oid
            for oid in order_ids
        }
        for future in as_completed(futures):
            oid = futures[future]
            carriers[index_map[oid]] = future.result()

    return carriers
