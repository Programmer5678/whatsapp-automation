from datetime import datetime, timedelta
import logging
from zoneinfo import ZoneInfo


# SQLAlchemy
from sqlalchemy import text

# Typing / other standard libs (if needed)
# from typing import ...

# Project-specific imports
from api.base_models import SendMassMessagesRequestModel
from shared.timezone import TIMEZONE
from shared.exception_to_json import exception_to_json
from db.get_cursor import get_cursor

# WhatsApp core
from whatsapp.core.evo_request import evo_request_with_retries
from whatsapp.core.core import _phone_number
from whatsapp.core.whatsapp_connection import validate_whatsapp_connection
from whatsapp.whatsapp_group.core.compute_spread_times import compute_spread_times

# Job and listener
from job_and_listener.job.core.create.create_job import create_job
from job_and_listener.job.models.job_model import JobMetadata, JobAction, JobSchedule, Job
from job_and_listener.job_batch.core import create_job_batch


SEND_MASS_MESSAGES_BATCH_ID = "send_mass_messages_batch"
   
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
        
        logging.debug if use_logging else print
        
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
            batch_id=SEND_MASS_MESSAGES_BATCH_ID,
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

        job = Job(metadata=metadata, action=action, schedule=schedule)
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
    
    
    # --- Insert participants into mass_messages table ---
    insert_participants_to_sql(cur, payload.participants)

    create_job_batch(SEND_MASS_MESSAGES_BATCH_ID, cur)

    # schedule the jobs
    schedule_mass_messages_jobs(sched, cur, [part.phone_number for part in payload.participants], payload.message)
    
    return {"message": "Mass messages scheduling initiated."}
