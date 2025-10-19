from dataclasses import dataclass
from typing import List, Dict, Any

from evo_request import evo_request
    

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



# --- STEP 4: Get invite link (unchanged) ---
def get_group_invite_link(group_id: str) -> str:
    resp = evo_request(f"group/inviteCode", get=True, params={"groupJid": group_id})
    # some APIs return inviteUrl / inviteLink / link — try common keys
    return resp.get("inviteUrl") or resp.get("inviteLink") or resp.get("link")







