# #!/usr/bin/env python3
# import os
# import argparse
import requests
import json

# Define restricted methods that require {"method": ..., "args": ...}
RESTRICTED_METHODS = {
    "sendText",
    "createGroup",
    "getAllMessagesInChat",
    "videoCall",
    "call",
    "getGroupInviteLink",
}

def wa_request(api_url, method_or_endpoint, args=None, timeout=10):
    """
    Call any open-wa REST API method or endpoint.

    :param api_url: Base URL of wa-automate REST API, e.g., "http://localhost:8080"
    :param method_or_endpoint: Either a restricted method name (sendText, createGroup, etc.)
                               or a direct endpoint like "getAllChats"
    :param args: dict of arguments for the method/endpoint
    :param timeout: request timeout
    :return: JSON response if available, else raw text
    """
    args = args or {}

    # Determine if we should use the legacy "method"/"args" style
    if method_or_endpoint in RESTRICTED_METHODS:
        payload = {"method": method_or_endpoint, "args": args}
        url = api_url  # restricted methods use the root endpoint
    else:
        payload = args
        url = f"{api_url}/{method_or_endpoint}"  # direct endpoints

    try:
        r = requests.post(url, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise RuntimeError(f"Request {payload} failed: {e}") from e

    print(f"Request {method_or_endpoint}, {payload} =>")
    print("status:", r.status_code)

    try:
        data = r.json()
        print("body:", json.dumps(data, indent=4, ensure_ascii=False))
        return data
    except json.JSONDecodeError:
        raise Exception("body is not valid JSON:", r.text)
        return r.text


# --- Examples of usage ---

wa_api = "http://localhost:8080"


def _contact_id(number):
    return number + "@c.us"

def create_group(name, participants):
    """Step 1: create group and return raw response"""
    return wa_request(
        wa_api,
        "createGroup",
        {
            "groupName": name,
            "contacts": [_contact_id(p) for p in participants]
        }
    )

def extract_gid_from_create_resp(group_resp):
    """Extract gid from createGroup response (same assumptions as original)"""
    return group_resp.get("gid") or group_resp.get("groupId") or group_resp.get("response", {}).get("_serialized")

def send_messages_to_group(gid, messages):
    """Step 2: send initial messages to group"""
    for msg in messages:
        wa_request(
            wa_api,
            "sendText",
            {"to": gid, "content": msg}
        )

def get_group_member_ids(gid):
    """Return only the list of member IDs"""
    result = wa_request(
        wa_api,
        "getGroupMembers",
        {"groupId": gid}
    )
    members = result.get("response", [])
    return [m["id"] for m in members if "id" in m]
    

def compute_failed_to_add(participants, actual_members):
    """Step 3: compute participants who failed to be added"""
    return [p for p in participants if _contact_id(p) not in actual_members]

def get_group_invite_link(gid):
    """Step 4: get group invite link"""
    invite_info = wa_request(
        wa_api,
        "getGroupInviteLink",
        {"chatId": gid}
    )
    return invite_info.get("response", [])

def send_invite_to_failed(failed_to_add, invite_link, invite_msg_title):
    """Step 5: send invite message to those who failed"""
    # for p in failed_to_add:
    #     wa_request(
    #         wa_api,
    #         "sendLinkWithAutoPreview",
    #         {
    #             "to": _contact_id(p),
    #             "url": invite_link,
    #             "text": invite_msg_title,
    #         }
    #     )
    message = f"{invite_msg_title}\n\n{invite_link}"
    for participant in failed_to_add:
        wa_request(
            wa_api,
            "sendText",
            {
                "to": _contact_id(participant),
                "content": message,
            },
        )
    

def handle_failed_adds(gid, participants, invite_msg_title):
    """Perform steps 3, 4 and 5 (as requested: grouped into one function)."""
    members_resp = get_group_member_ids(gid)
    actual_members = set(members_resp)
    failed_to_add = compute_failed_to_add(participants, actual_members)

    if failed_to_add:
        invite_link = get_group_invite_link(gid)
        send_invite_to_failed(failed_to_add, invite_link, invite_msg_title)

def create_group_and_invite(name, participants, messages, invite_msg_title):
    # Create group
    group_resp = create_group(name, participants)

    gid = extract_gid_from_create_resp(group_resp)
    if not gid:
        raise RuntimeError(f"Could not find group ID in response: {json.dumps(group_resp, indent=4, ensure_ascii=False)}")

    # Send initial messages to the group
    send_messages_to_group(gid, messages)


    input("Press Enter to continue...")  # Pause for user to see the response
    # Steps 3,4,5 grouped
    handle_failed_adds(gid, participants, invite_msg_title)


