import requests
from typing import Optional, Any
from time import sleep
# from logging import getLogger

from .logger import logger

def request_with_retry(
    method: str,
    url: str,
    max_retries: int = 5,
    timeout0: int = 5,
    backoff_factor: float = 1.0,
    retry_on_status: Optional[list] = None,
    **kwargs: Any
) -> requests.Response:
    """
    Wrapper for requests with automatic retry and timeout handling.
    
    Args:
        method: HTTP method ('GET', 'POST', 'PUT', 'DELETE', etc.)
        url: The URL to request
        max_retries: Maximum number of retry attempts (default: 5)
        timeout0: Base request timeout in seconds (default: 5)
        backoff_factor: Multiplier for exponential backoff between retries (default: 1.0)
                       Wait time = backoff_factor * (2 ** retry_number)
        retry_on_status: List of HTTP status codes to retry on (default: [500, 502, 503, 504])
        **kwargs: All other arguments are passed directly to requests.request()
                 (params, data, json, headers, cookies, auth, files, etc.)
    
    Returns:
        requests.Response object
        
    Raises:
        requests.exceptions.RequestException: If all retries are exhausted
    """
    if retry_on_status is None:
        retry_on_status = [500, 502, 503, 504]
    
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.request(
                method, url, timeout=timeout0+2*attempt, **kwargs
            )
            
            # Check if we should retry based on status code
            if response.status_code in retry_on_status and attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt)
                if attempt > 1:
                    logger.debug(f"Attempt {attempt + 1} failed with status {response.status_code}. "
                      f"Retrying in {wait_time}s...\t{url}")
                sleep(wait_time)
                continue
            
            # Return response even if status is not 2xx (let caller handle it)
            return response
            
        except (requests.exceptions.Timeout, 
                requests.exceptions.ConnectionError,
                requests.exceptions.RequestException) as e:
            last_exception = e
            
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt)
                if attempt > 1:
                    logger.debug(f"Attempt {attempt + 1} failed: {type(e).__name__}. "
                      f"Retrying in {wait_time}s...\t{url}")
                sleep(wait_time)
            else:
                # All retries exhausted
                raise requests.exceptions.RequestException(
                    f"Failed after {max_retries + 1} attempts. Last error: {str(e)}"
                ) from last_exception
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def get_with_retry(
    url: str,
    max_retries: int = 5,
    timeout0: int = 5,
    backoff_factor: float = 1.0,
    retry_on_status: Optional[list] = None,
    **kwargs: Any
) -> requests.Response:
    """
    Wrapper for requests.get() with automatic retry and timeout handling.
    
    Args:
        url: The URL to request
        max_retries: Maximum number of retry attempts (default: 5)
        timeout0: Base request timeout in seconds (default: 5)
        backoff_factor: Multiplier for exponential backoff between retries (default: 1.0)
                       Wait time = backoff_factor * (2 ** retry_number)
        retry_on_status: List of HTTP status codes to retry on (default: [500, 502, 503, 504])
        **kwargs: All other arguments are passed directly to requests.get()
                 (params, headers, cookies, auth, etc.)
    
    Returns:
        requests.Response object
        
    Raises:
        requests.exceptions.RequestException: If all retries are exhausted
        
    Example:
        response = get_with_retry(
            'https://api.example.com/data',
            params={'key': 'value'},
            headers={'Authorization': 'Bearer token'},
            max_retries=5,
            timeout0=15
        )
    """
    return request_with_retry(
        'GET', url, max_retries, timeout0, backoff_factor, retry_on_status, **kwargs
    )


def post_with_retry(
    url: str,
    max_retries: int = 5,
    timeout0: int = 5,
    backoff_factor: float = 1.0,
    retry_on_status: Optional[list] = None,
    **kwargs: Any
) -> requests.Response:
    """
    Wrapper for requests.post() with automatic retry and timeout handling.
    
    Args:
        url: The URL to request
        max_retries: Maximum number of retry attempts (default: 5)
        timeout0: Base request timeout in seconds (default: 5)
        backoff_factor: Multiplier for exponential backoff between retries (default: 1.0)
                       Wait time = backoff_factor * (2 ** retry_number)
        retry_on_status: List of HTTP status codes to retry on (default: [500, 502, 503, 504])
        **kwargs: All other arguments are passed directly to requests.post()
                 (data, json, headers, cookies, auth, files, etc.)
    
    Returns:
        requests.Response object
        
    Raises:
        requests.exceptions.RequestException: If all retries are exhausted
        
    Example:
        response = post_with_retry(
            'https://api.example.com/data',
            json={'key': 'value'},
            headers={'Authorization': 'Bearer token'},
            max_retries=5,
            timeout0=15
        )
    """
    return request_with_retry(
        'POST', url, max_retries, timeout0, backoff_factor, retry_on_status, **kwargs
    )