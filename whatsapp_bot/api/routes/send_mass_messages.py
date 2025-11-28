from fastapi import APIRouter, Depends, status
from sqlalchemy import text

from setup import get_cursor_dep
from mass_messages import send_mass_messages_service
from models import SendMassMessagesRequestModel
from setup import get_scheduler

messages_router = APIRouter()


@messages_router.post("/send_mass_messages", status_code=status.HTTP_201_CREATED)
def send_mass_messages_route(
    payload: SendMassMessagesRequestModel,
    cur = Depends(get_cursor_dep),
    scheduler = Depends(get_scheduler)
):
    return send_mass_messages_service(scheduler, cur, payload)
