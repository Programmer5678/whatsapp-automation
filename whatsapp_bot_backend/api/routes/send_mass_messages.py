from fastapi import APIRouter, Depends, status

from api.dependencies import get_cursor_dep, get_scheduler
from whatsapp.mass_messages.service import send_mass_messages_service
from api.base_models import SendMassMessagesRequestModel

messages_router = APIRouter()


@messages_router.post("/send_mass_messages", status_code=status.HTTP_201_CREATED)
def send_mass_messages_route(
    payload: SendMassMessagesRequestModel,
    cur = Depends(get_cursor_dep),
    scheduler = Depends(get_scheduler)
):
    return send_mass_messages_service(scheduler, cur, payload)
