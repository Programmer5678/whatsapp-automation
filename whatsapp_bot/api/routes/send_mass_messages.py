from fastapi import APIRouter, Depends, status
from sqlalchemy import text

from api.dependencies import get_cursor_dep
from whatsapp_bot.whatsapp.mass_messages import send_mass_messages_service
from whatsapp_bot.api.base_models import SendMassMessagesRequestModel
from whatsapp_bot.api.setup.setup import get_scheduler

messages_router = APIRouter()


@messages_router.post("/send_mass_messages", status_code=status.HTTP_201_CREATED)
def send_mass_messages_route(
    payload: SendMassMessagesRequestModel,
    cur = Depends(get_cursor_dep),
    scheduler = Depends(get_scheduler)
):
    return send_mass_messages_service(scheduler, cur, payload)
