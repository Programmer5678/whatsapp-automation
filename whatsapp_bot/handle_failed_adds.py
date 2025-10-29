
from typing import List
from warnings import warn
from evolution_framework import _phone_number, get_group_invite_link, get_group_member_ids
from evo_request import evo_request_with_retries
import time


def compute_failed_to_add(participants: List[str], actual_members: set) -> List[str]:
    """Return list of normalized participants that were not added to the group."""
    return [_phone_number(p) for p in participants if _phone_number(p) not in actual_members]





# def send_invite_to_failed(failed_to_add: List[str], invite_link: str, invite_msg_title: str) -> None:
#     """
#     Send invite messages to participants who failed to be added previously.
#     Uses MassMessenger class internally.
#     """
#     message = f"{invite_msg_title}\n\n{invite_link}"
    
#     messenger = MassMessenger(
#         numbers=failed_to_add,
#         message=message
#         # No callbacks passed, so behaves like original function
#     )
    
#     messenger.send_all()


# --- STEP 5: Send invite to failed participants (unchanged signature) ---
def send_invite_to_failed(failed_to_add: List[str], invite_link: str, invite_msg_title: str) -> None:
    
        
    message = f"{invite_msg_title}\n\n{invite_link}"
    for p in failed_to_add:
        
        resp = evo_request_with_retries(
                "message/sendText",
                {
                    "number": _phone_number(p),
                    "text": message,
                    "delay": 50000
                }
            )
        
        
        try: # if resp is error because participant doesnt exist --> just warn and handle
            assert resp.json()["response"]["message"][0]["exists"] is False
            warn(f"Participant {p} does not exist — skipping.")
        except Exception:
            resp.raise_for_status()
       
        time.sleep(10)
        
    


def handle_failed_adds(participants: list[str], invite_msg_title: str, group_id: str) -> None:
    """
    Handle failed participant additions and send them an invite link.
    """
    actual_members = set(get_group_member_ids(group_id))
    failed_to_add = compute_failed_to_add(participants, actual_members)

    if failed_to_add:
        invite_link = get_group_invite_link(group_id)
        send_invite_to_failed(failed_to_add, invite_link, invite_msg_title)

    
    