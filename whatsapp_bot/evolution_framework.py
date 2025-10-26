from dataclasses import dataclass
from typing import List, Dict, Any

from evo_request import evo_request, evo_request_with_retries
    

# --- STEP 0: normalize phone numbers ---
def _phone_number(phone: str) -> str:
    """Evolution API expects only digits, no + or @c.us"""
    return ''.join(filter(str.isdigit, str(phone)))



# --- STEP 3: Get group members (unchanged signature) ---
def get_group_member_ids(group_id: str) -> List[str]:
    """
    Returns list of participants' phone numbers (as strings).
    Uses Evolution API /group/participants endpoint with query parameter 'groupJid'.
    """
        
    resp_json = evo_request_with_retries(
        "group/participants",
        get=True,
        params={"groupJid": group_id}
    ).json()

    participants = resp_json.get("participants", []) or []

    out = []
    for p in participants:

        candidate = p.get("phoneNumber")
        if candidate:
            out.append(_phone_number(candidate))
    return out



# --- STEP 4: Get invite link (unchanged) ---
def get_group_invite_link(group_id: str) -> str:
    resp_json = evo_request_with_retries(f"group/inviteCode", get=True, params={"groupJid": group_id}).json()

    return resp_json.get("inviteUrl") 







