from datetime import datetime, timedelta
import logging
import traceback
from zoneinfo import ZoneInfo

from sqlalchemy import text, bindparam

from whatsapp_bot.api.base_models import SendMassMessagesRequestModel
from db import get_cursor
from whatsapp_bot.core.timezone import TIMEZONE

from whatsapp.core.evo_request import evo_request_with_retries
# If these are not used in this file, also remove:
from whatsapp_bot.whatsapp.core.whatsapp_connection import validate_whatsapp_connection
from whatsapp_group.core.compute_spread_times import compute_spread_times
from whatsapp_bot.core.exception_to_json import exception_to_json
from job_and_listener.job.core.create.create_job import create_job
from datetime import datetime, timedelta
from job_and_listener.job.models.job_to_create_model import JobMetadata, JobAction, JobSchedule, JobToCreate
from whatsapp.core import _phone_number

# def calculate_relevant_participants(cur, participants):
#     """
#     Returns only participants whose IDs are not marked success=TRUE in mass_messages.

#     Args:
#         cur: Active database cursor or SQLAlchemy connection.
#         participants: List of participant objects (must have 'id' attribute).

#     Returns:
#         List of participants still relevant for sending.
#     """
#     if not participants:
#         return []

#     ids = [p.id for p in participants]

#     res = cur.execute(
#         text("SELECT id FROM mass_messages WHERE id IN :ids AND success = TRUE").bindparams( bindparam("ids", expanding=True) )
#         , {"ids": ids}
#     ).fetchall()

#     already_success_ids = {row[0] for row in res }

#     return [p for p in participants if p.id not in already_success_ids]
   
   
   
   
# --- Define callbacks ---
def mark_message_success_in_sql(cur, phone_number: str):
    """
    Marks a message as successfully sent in the mass_messages table.
    """
    cur.execute(
        text("UPDATE mass_messages SET success = TRUE WHERE phone_number = :phone_number"),
        {"phone_number": phone_number}
    )


def mark_message_failure_in_sql(cur, phone_number: str, reason: str):
    """
    Marks a message as failed in the mass_messages table and records the failure reason.
    """
    cur.execute(
        text("""
            UPDATE mass_messages
            SET success = FALSE, fail_reason = :reason
            WHERE phone_number = :phone_number
        """),
        {"phone_number": phone_number, "reason": reason}
    )
   
   
   
   
def mass_messages_job(job_name, run_args, use_logging=True):
    """
    Job that sends a WhatsApp message and records success/failure in the database.

    Args:
        job_name: APScheduler job name (not used here, but passed by scheduler)
        run_args: dict containing:
            - "message": the text to send
            - "p": recipient phone number
    """
    with get_cursor() as cur:
        
        log = logging.debug if use_logging else print
        
        try:
            # Send the message via the API
            resp = evo_request_with_retries(
                "message/sendText",
                {
                    "number": _phone_number(run_args["p"]),
                    "text": run_args["message"],
                    "delay": 50000,  # some delay required by API
                },
            )

            # If the response is not OK, raise an exception
            if not resp.ok: 
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

        except Exception as e:  # Record failure in SQL
            # Capture full traceback and store it in DB
            
            # mark_message_failure_in_sql(cur, run_args["p"], "failed")
            # log(exception_to_json(e))
            mark_message_failure_in_sql(cur, run_args["p"], exception_to_json(e))
            raise  # Re-raise so the scheduler knows this job failed

        # If message was sent successfully, mark it as success in DB
        mark_message_success_in_sql(cur, run_args["p"])


# ...existing code...
from whatsapp_bot.whatsapp.core.evo_request import evo_request_with_retries
from evolution_framework import _phone_number
from job_and_listener.job.core.create.create_job import create_job

# ...existing code...

def schedule_mass_messages_jobs(scheduler, cur, numbers, message):
    """
    Schedule sending messages to a list of numbers, one per minute starting 30s from now.

    Args:
        cur: DB cursor
        numbers: list of phone numbers
        message: message text to send
    """
    # First scheduled time is 30 seconds from now
    start = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=30)
    run_times = compute_spread_times( start, min_diff = timedelta(minutes=1.5) , runs=len(numbers) )

    for p, run_time in zip(numbers, run_times):

        # Create an APScheduler job for this message
        metadata = JobMetadata(
            id="send_message_to_" + p + "_" + run_time.strftime("%Y%m%d%H%M%S"),
            description="",
            batch_id="send_mass_messages_batch",
        )

        action = JobAction(
            func=mass_messages_job,
            run_args={"message": message, "p": p},
        )

        schedule = JobSchedule(
            run_time=run_time,
           coalesce=True,
            misfire_grace_time=1,
        )

        job = JobToCreate(metadata=metadata, action=action, schedule=schedule)
        create_job(cur, scheduler, job)
# ...existing code...


def insert_participants_to_sql(cur, participants):
    """
    Inserts a list of participants into the mass_messages table.
    Skips any duplicates based on the primary key 'id'.

    Args:
        cur: Active DB cursor
        participants: List of participant objects with 'id' and 'phone_number' attributes
    """
    insert_sql = text("""
        INSERT INTO mass_messages (id, phone_number, success)
        VALUES (:id, :phone_number, :success)
        ON CONFLICT (id) DO NOTHING
    """)

    for part in participants:
        cur.execute(
            insert_sql,
            {
                "id": part.id,
                "phone_number": part.phone_number,
                "success": None
            }
        )

def send_mass_messages_service(sched, cur, payload: SendMassMessagesRequestModel):
    validate_whatsapp_connection() 
    
    # ids = [part.id for part in payload.participants]  
    # phone_numbers = [part.phone_number for part in payload.participants] 
    
    # if len(set(ids)) != len(ids) or len(set(phone_numbers)) != len(phone_numbers):
    #     raise Exception("Duplicate participant IDs or phone numbers found in the payload.")
    
    
    
    # --- Insert participants into mass_messages table ---
    insert_participants_to_sql(cur, payload.participants)

    # schedule the jobs
    schedule_mass_messages_jobs(sched, cur, [part.phone_number for part in payload.participants], payload.message)
    
    return {"message": "Mass messages scheduling initiated."}
