from dataclasses import dataclass
from typing import List
from whatsapp_bot.whatsapp.core.evo_request import evo_request, evo_request_with_retries
from sqlalchemy import text
from whatsapp.core.evo_request import evo_request_with_retries
from whatsapp.core.core import _phone_number



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





# core.py (actual logic)
def get_group_participants(gid: str, excluded: list[str]) -> dict:
    """
    Calls the EVO API, maps participants to phone numbers,
    and filters out excluded participants.
    """
    resp = evo_request_with_retries(
        method="/group/participants",
        get=True,
        params={"groupJid": gid}
    )
    participants_json = resp.json().get("participants", [])
    all_numbers = [_phone_number(p["phoneNumber"]) for p in participants_json]

    all_numbers_without_excluded = [n for n in all_numbers if n not in excluded]
    excluded_that_not_in_group = [n for n in excluded if n not in all_numbers]

    return {
        "all_numbers_without_excluded": all_numbers_without_excluded,
        "excluded_that_not_in_group": excluded_that_not_in_group,
        "all_numbers": all_numbers,
    }

