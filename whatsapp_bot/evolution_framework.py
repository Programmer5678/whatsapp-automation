from dataclasses import dataclass
from typing import List, Dict, Any


from schedule_create_group import schedule_deadline_jobs
from apscheduler.schedulers.background import BackgroundScheduler
from evo_request import evo_request
from send_stuff_to_group import send_stuff
from classes import WhatsappGroupCreate
    

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


def debug():
    print("debug")
    

# --- FULL FLOW (now accepts WhatsappGroupCreate) ---
def create_group_and_invite(req: WhatsappGroupCreate, description: str = "") -> str:
    group_id = create_group(req, description)
    if not group_id:
        raise RuntimeError("Failed to create group or no group ID returned")

    send_stuff(req.media , req.messages, group_id)

    # input("Press Enter to continue to handle failed adds...")
    
    # schedule_deadline_jobs( lambda : handle_failed_adds(req, group_id) ,  req.deadline, req.sched )
    
    schedule_deadline_jobs( req, group_id )
    
    return group_id


# Example usage:
# from somewhere import WhatsappGroupCreate
# req = WhatsappGroupCreate(messages=[...], name="מבדק DATE", participants=["972532237008"], invite_msg_title="...", media=[])
# gid = create_group_and_invite(req)
