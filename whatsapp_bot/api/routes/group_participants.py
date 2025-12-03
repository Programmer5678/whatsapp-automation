from fastapi import APIRouter, Depends, status

from api.base_models import ChangeParticipantsRequestModel, GetParticipantsRequestModel
from whatsapp.core.whatsapp_connection import validate_whatsapp_connection
from api.dependencies import get_cursor_dep

from whatsapp.whatsapp_group.features.participants.service import change_participants_service, get_group_participants_service

participants_router = APIRouter()


@participants_router.post("/get_participants")
# route.py
def get_group_participants_route(req: GetParticipantsRequestModel) -> dict:
    """
    API route layer: one-liner calling the service.
    """
    return get_group_participants_service(req.gid, req.participants_to_exclude)



@participants_router.post("/change_participants", status_code=status.HTTP_201_CREATED)
def change_participants_route(
    req: ChangeParticipantsRequestModel,
    cur=Depends(get_cursor_dep),
):
    """
    Ensures WhatsApp connection is valid, then updates participants in the DB.
    """
    validate_whatsapp_connection()
    change_participants_service(cur, req.gid, req.participants)

    return {
        "message": "Participants updated successfully in DB. Will be used as source of truth next job"
    }
