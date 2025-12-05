from api.base_models import SendMassMessagesRequestModel
from job_and_listener.job_batch.core import create_job_batch
from whatsapp.core.whatsapp_connection import validate_whatsapp_connection
from whatsapp.mass_messages.mass_messages import SEND_MASS_MESSAGES_BATCH_ID, insert_participants_to_sql, schedule_mass_messages_jobs, send_mass_messages_core


def send_mass_messages_service(
    sched, cur, payload: SendMassMessagesRequestModel
):
    validate_whatsapp_connection()
    send_mass_messages_core(sched, cur, payload)
    return {"message": "Mass messages scheduling initiated."}


