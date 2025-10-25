from typing import Any
import requests
from pprint import pprint
from domain_errors import EvolutionServerError, JSONParseError

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
        if get:
            # resp = requests.get(url, headers=headers, params=params)
            
            resp = request_and_print( "GET", url, headers, params, json=payload ) #DEBUG
        else:
            # resp = requests.post(url, json=payload or {}, headers=headers)
            resp = request_and_print( "POST", url, headers, params, json=payload) #DEBUG

                        
        return resp
    

    except requests.exceptions.RequestException as e:
        raise EvolutionServerError(response = resp.json()) from e
    except ValueError as e:
        raise JSONParseError("[evo_request] Failed to parse JSON response") from e
    
