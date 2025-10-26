from typing import Any
import requests
from pprint import pprint
from domain_errors import ConnectionDomainError, EvolutionServerError, JSONParseError

# --- Config ---
BASE_URL = "http://localhost:8080"      # Evolution API URL
API_KEY = "ruz123"                      # Your API key
INSTANCE = "my_instance"                # WhatsApp instance ID


def request_and_print(method, url, headers=None, params=None, data=None, json=None):
    """
    Send a request with the given parameters and print the full request details
    before sending.
    """
    session = requests.Session()

    # Create and prepare the request
    req = requests.Request(
        method=method.upper(),
        url=url,
        headers=headers,
        params=params,
        data=data,
        json=json
    )
    prepped = session.prepare_request(req)

    # Print prepared request details
    print("=== REQUEST ===")
    print("Method:", prepped.method)
    print("URL:", prepped.url)
    print("Headers:")
    pprint(dict(prepped.headers))
    if prepped.body:
        print("Body:", prepped.body)
    print("================")

    # Send request and return response
    resp = session.send(prepped)

    # Print response details
    print("=== RESPONSE ===")
    print("Status:", resp.status_code)
    try:
        pprint(resp.json())
    except Exception:
        print(resp.text)
    print("================")

    return resp

def evo_request(method: str, payload: dict = None, get: bool = False, params: dict = None) -> Any:
    
    """
    Generalized request to Evolution API.
    """
    
    # print("\n\n")
    
    url = f"{BASE_URL}/{method}/{INSTANCE}"
    headers = {"Content-Type": "application/json", "apikey": API_KEY}

    try:
        resp = None
        if get:
            # resp = requests.get(url, headers=headers, params=params)
            
            resp = request_and_print( "GET", url, headers, params, json=payload ) #DEBUG
        else:
            # resp = requests.post(url, json=payload or {}, headers=headers)
            resp = request_and_print( "POST", url, headers, params, json=payload) #DEBUG

                        
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

def evo_request_with_retries(method: str, payload: dict = None, get: bool = False, params: dict = None) -> any:
    """
    Call evo_request with retry logic for connection errors.
    Wait times: 10 seconds, 5 minutes, 30 minutes, then raise the exception.
    """
    wait_times = [10, 300, 1800]  # seconds: 10s, 5min, 30min

    for attempt, wait in enumerate(wait_times, start=1):
        try:
            return evo_request(method, payload=payload, get=get, params=params)
        except ConnectionDomainError as e:
            warnings.warn(f"[Attempt {attempt}] Connection failed: {e}. Retrying in {wait} seconds...")
            time.sleep(wait)
    
    # Last attempt: just call one more time, let it raise if fails
    return evo_request(method, payload=payload, get=get, params=params)
    
