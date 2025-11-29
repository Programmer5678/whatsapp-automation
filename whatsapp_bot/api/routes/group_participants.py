from fastapi import APIRouter, Depends, status
from sqlalchemy import text  # optional if you plan to run SQL here later

from models import ChangeParticipantsRequestModel, GetParticipantsRequestModel
from connection import validate_whatsapp_connection
from api.dependencies import get_cursor_dep
from evo_request import evo_request_with_retries
from evolution_framework import _phone_number
from dynamic_group_changes import change_participants

participants_router = APIRouter()


@participants_router.post("/get_participants")
def get_participants_route(req: GetParticipantsRequestModel):
    """
    Calls the evo API to get group participants, maps to phone numbers,
    and filters out excluded participants from the request.
    """
    resp = evo_request_with_retries(method="/group/participants", get=True, params={"groupJid": req.gid})
    participants_json = resp.json().get("participants", [])
    all_numbers_id = [p["phoneNumber"] for p in participants_json]
    all_numbers = [_phone_number(p) for p in all_numbers_id]

    all_numbers_without_excluded = [n for n in all_numbers if n not in req.participants_to_exclude]
    excluded_that_not_in_group = [n for n in req.participants_to_exclude if n not in all_numbers]

    return {
        "all_numbers_without_excluded": all_numbers_without_excluded,
        "excluded_that_not_in_group": excluded_that_not_in_group,
        "all_numbers": all_numbers,
    }


@participants_router.post("/change_participants", status_code=status.HTTP_201_CREATED)
def change_participants_route(
    req: ChangeParticipantsRequestModel,
    cur=Depends(get_cursor_dep),
):
    """
    Ensures WhatsApp connection is valid, then updates participants in the DB.
    """
    validate_whatsapp_connection()
    change_participants(cur, req.gid, req.participants)

    return {
        "message": "Participants updated successfully in DB. Will be used as source of truth next job"
    }
