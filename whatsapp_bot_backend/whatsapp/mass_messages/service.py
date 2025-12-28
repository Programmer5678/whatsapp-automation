from api.base_models import SendMassMessagesRequestModel
from whatsapp.core.whatsapp_connection import validate_whatsapp_connection
from whatsapp.mass_messages.mass_messages import send_mass_messages_core


def send_mass_messages_service(
    sched, cur, payload: SendMassMessagesRequestModel
):
    validate_whatsapp_connection()
    send_mass_messages_core(sched, cur, payload)
    return {"message": "Mass messages scheduling initiated."}


