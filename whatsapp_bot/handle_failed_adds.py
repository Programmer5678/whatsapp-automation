
from typing import List
from evolution_framework import _phone_number, get_group_invite_link, get_group_member_ids
from evo_request import evo_request
from classes import WhatsappGroupCreate

def compute_failed_to_add(participants: List[str], actual_members: set) -> List[str]:
    """Return list of normalized participants that were not added to the group."""
    return [_phone_number(p) for p in participants if _phone_number(p) not in actual_members]

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