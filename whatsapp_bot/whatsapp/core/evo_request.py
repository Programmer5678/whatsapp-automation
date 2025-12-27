import logging
from typing import Any
import requests
from pprint import pformat
from shared.domain_errors import ConnectionDomainError, EvolutionServerError, JSONParseError

# --- Config ---
BASE_URL = "http://localhost:8080"      # Evolution API URL
API_KEY = "ruz123"                      # Your API key
INSTANCE = "my_instance"                # WhatsApp instance ID



def request_and_print(method, url, headers=None, params=None, data=None, json=None, use_logging=False):
    """
    Send an HTTP request and log or print the full request/response details.

    Args:
        method (str): HTTP method ("GET", "POST", etc.)
        url (str): The URL to request.
        headers (dict, optional)
        params (dict, optional)
        data (dict, optional)
        json (dict, optional)
        use_logging (bool): If True, use logging.debug instead of print().
    """
    log = logging.debug if use_logging else print
    session = requests.Session()

    # Prepare request
    req = requests.Request(method.upper(), url, headers=headers, params=params, data=data, json=json)
    prepped = session.prepare_request(req)

    # === REQUEST ===
    log("=== REQUEST ===")
    log(f"Method: {prepped.method}")
    log(f"URL: {prepped.url}")
    log(f"Headers:\n{pformat(dict(prepped.headers))}")
    if prepped.body:
        log(f"Body: {prepped.body}")
    log("================")

    # Send request
    resp = session.send(prepped)

    # === RESPONSE ===
    log("=== RESPONSE ===")
    log(f"Status: {resp.status_code}")
    try:
        log(pformat(resp.json()))
    except Exception:
        log(resp.text)
    log("================")

    return resp


def evo_request(path: str, payload: dict = None, params: dict = None, method: str = "POST", no_suffix: bool = False) -> Any:
    
    """
    Generalized request to Evolution API.
    """
    
    # print("\n\n")

    url = f"{BASE_URL}/{path}/{INSTANCE}" if not no_suffix else f"{BASE_URL}/{path}"
    headers = {"Content-Type": "application/json", "apikey": API_KEY}

    try:
        
        resp = request_and_print( method, url, headers, params, json=payload ) #DEBUG
        return resp


    except requests.exceptions.ConnectionError as e:
        raise ConnectionDomainError from e

    except requests.exceptions.RequestException as e:
        if isinstance( resp, requests.Response):
            raise EvolutionServerError(response = resp.json()) from e
        raise  EvolutionServerError() from e
        
    except ValueError as e:
        raise JSONParseError("[evo_request] Failed to parse JSON response") from e
    
    
# created this especially to deal with ConnectionError caused by ConnectionResetError.
# This happened when i ran get participantss request immediately after updating participants.
import warnings
import time

def evo_request_with_retries(path: str, payload: dict = None, params: dict = None, method: str = "POST", no_suffix: bool = False) -> any:
    """
    Call evo_request with retry logic for connection errors.
    Wait times: 10 seconds, 5 minutes, 30 minutes, then raise the exception.
    """
    wait_times = [10, 20]  # seconds: 10s, 5min, 30min

    for attempt, wait in enumerate(wait_times, start=1):
        try:
            return evo_request(path, payload=payload, params=params, method=method, no_suffix=no_suffix)
        except ConnectionDomainError as e:
            warnings.warn(f"[Attempt {attempt}] Connection failed: {e}. Retrying in {wait} seconds...")
            time.sleep(wait)
    
    # Last attempt: just call one more time, let it raise if fails
    return evo_request(path, payload=payload, params=params)
    
