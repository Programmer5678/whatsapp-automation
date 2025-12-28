
from whatsapp.whatsapp_group.features.participants.core import get_group_participants
from whatsapp.whatsapp_group.features.participants.db import change_participants


def get_group_participants_service(gid: str, excluded: list[str]) -> dict:
    """
    Service layer: calls the core logic function.
    """
    return get_group_participants(gid, excluded)


def change_participants_service(cur, group_id: str, new_participants: list[str]) -> None:
    """
    Service layer: calls the core logic function to change participants in the DB.
    """
    change_participants(cur, group_id, new_participants)