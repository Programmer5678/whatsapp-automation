from whatsapp.core.evo_request import evo_request_with_retries


def get_group_invite_link(group_id: str) -> str:
    resp_json = evo_request_with_retries(f"group/inviteCode", get=True, params={"groupJid": group_id}).json()

    return resp_json.get("inviteUrl") 