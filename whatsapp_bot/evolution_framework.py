from dataclasses import dataclass
from typing import List, Dict, Any

import requests

# --- Simple container you asked for ---
@dataclass
class WhatsappGroupCreate:
    messages: List[str]
    name: str
    participants: List[str]
    invite_msg_title: str
    media: List[str]


# --- Config (unchanged) ---
BASE_URL = "http://localhost:8080"      # Evolution API URL
API_KEY = "ruz123"                      # Your API key
INSTANCE = "my_instance"                # WhatsApp instance ID


def evo_request(method: str, payload: dict = None, get: bool = False, params: dict = None) -> Any:
    
    """
    Generalized request to Evolution API.
    """
    
    print("\n\n")
    
    url = f"{BASE_URL}/{method}/{INSTANCE}"
    headers = {"Content-Type": "application/json", "apikey": API_KEY}

    try:
        if get:
            resp = requests.get(url, headers=headers, params=params)
        else:
            resp = requests.post(url, json=payload or {}, headers=headers)
        resp.raise_for_status()
        
        print("\n\n")
        return resp.json()
    except requests.exceptions.RequestException as e:
        raise Exception(f"[evo_request] Request {url} \nHeaders: {headers} \nPayload: {payload} \nParams: {params} ") from e
    except ValueError as e:
        raise Exception("[evo_request] Failed to parse JSON response") from e
    
    



# --- STEP 0: normalize phone numbers ---
def _phone_number(phone: str) -> str:
    """Evolution API expects only digits, no + or @c.us"""
    return ''.join(filter(str.isdigit, str(phone)))


# --- STEP 1: Create group (now accepts WhatsappGroupCreate) ---
def create_group(req: WhatsappGroupCreate, description: str = "") -> str:
    """
    Create group with Evolution API v2.
    Returns the group ID.
    """
    payload = {
        "subject": req.name,
        "description": description,
        "participants": [_phone_number(p) for p in req.participants],
    }

    resp = evo_request("group/create", payload)
    return resp.get("id")


# --- STEP 2: Send messages to group (accepts WhatsappGroupCreate) ---
def send_messages_to_group(messages : List[str] , group_id: str) -> None:
    for msg in messages:
        evo_request(
            "message/sendText",
            {
                "number": group_id,   # group IDs work here
                "text": msg
            }
        )


def send_medias_to_group(medias, group_id: str) -> None:
    for m in medias:
        evo_request(
            "message/sendMedia",
            {
                "number": group_id,   # group IDs work here
                "mediatype": "image",
                "mimetype": "image/jpeg",
                "fileName": "image.jpeg",
                "caption": "",
                "media" : m
            }
        )

# --- STEP 3: Get group members (unchanged signature) ---
def get_group_member_ids(group_id: str) -> List[str]:
    """
    Returns list of participants' phone numbers (as strings).
    Uses Evolution API /group/participants endpoint with query parameter 'groupJid'.
    """
    resp = evo_request(
        "group/participants",
        get=True,
        params={"groupJid": group_id}
    )

    participants = resp.get("participants", []) or []

    out = []
    for p in participants:
        # tolerate a few possible field names returned by different APIs
        candidate = p.get("phoneNumber") or p.get("id") or p.get("participant") or p.get("user")
        if candidate:
            out.append(_phone_number(candidate))
    return out


def compute_failed_to_add(participants: List[str], actual_members: set) -> List[str]:
    """Return list of normalized participants that were not added to the group."""
    return [_phone_number(p) for p in participants if _phone_number(p) not in actual_members]


# --- STEP 4: Get invite link (unchanged) ---
def get_group_invite_link(group_id: str) -> str:
    resp = evo_request(f"group/inviteCode", get=True, params={"groupJid": group_id})
    # some APIs return inviteUrl / inviteLink / link — try common keys
    return resp.get("inviteUrl") or resp.get("inviteLink") or resp.get("link")


# --- STEP 5: Send invite to failed participants (unchanged signature) ---
def send_invite_to_failed(failed_to_add: List[str], invite_link: str, invite_msg_title: str) -> None:
    message = f"{invite_msg_title}\n\n{invite_link}"
    for p in failed_to_add:
        evo_request(
            "message/sendText",
            {
                "number": _phone_number(p),
                "text": message
            }
        )


# --- STEP 3,4,5 COMBINED (now accepts WhatsappGroupCreate) ---
def handle_failed_adds(req: WhatsappGroupCreate, group_id: str) -> None:
    actual_members = set(get_group_member_ids(group_id))
    failed_to_add = compute_failed_to_add(req.participants, actual_members)
    if failed_to_add:
        invite_link = get_group_invite_link(group_id)
        send_invite_to_failed(failed_to_add, invite_link, req.invite_msg_title)


# --- FULL FLOW (now accepts WhatsappGroupCreate) ---
def create_group_and_invite(req: WhatsappGroupCreate, description: str = "") -> str:
    group_id = create_group(req, description)
    if not group_id:
        raise RuntimeError("Failed to create group or no group ID returned")

    send_medias_to_group(req.media, group_id)
    send_messages_to_group(req.messages, group_id)

    # input("Press Enter to continue to handle failed adds...")
    handle_failed_adds(req, group_id)

    return group_id


# Example usage:
# from somewhere import WhatsappGroupCreate
# req = WhatsappGroupCreate(messages=[...], name="מבדק DATE", participants=["972532237008"], invite_msg_title="...", media=[])
# gid = create_group_and_invite(req)
