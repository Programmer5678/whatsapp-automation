from typing import  Any

import requests
from domain_errors import EvolutionServerError, JSONParseError

# --- Config (unchanged) ---
BASE_URL = "http://localhost:8080"      # Evolution API URL
API_KEY = "ruz123"                      # Your API key
INSTANCE = "my_instance"                # WhatsApp instance ID


def evo_request(method: str, payload: dict = None, get: bool = False, params: dict = None) -> Any:
    
    """
    Generalized request to Evolution API.
    """
    
    # print("\n\n")
    
    url = f"{BASE_URL}/{method}/{INSTANCE}"
    headers = {"Content-Type": "application/json", "apikey": API_KEY}

    try:
        if get:
            resp = requests.get(url, headers=headers, params=params)
        else:
            resp = requests.post(url, json=payload or {}, headers=headers)
                        
        resp_json = resp.json()                    
        resp.raise_for_status()
        
        return resp_json
    
    # finally:
    #     pass
    except requests.exceptions.RequestException as e:
        raise EvolutionServerError(response = resp_json) from e
    except ValueError as e:
        raise JSONParseError("[evo_request] Failed to parse JSON response") from e