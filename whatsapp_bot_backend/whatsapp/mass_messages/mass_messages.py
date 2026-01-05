from datetime import datetime, timedelta
import logging
from typing import Any, Dict, List
from zoneinfo import ZoneInfo


# SQLAlchemy
from sqlalchemy import text

# Typing / other standard libs (if needed)
# from typing import ...

# Project-specific imports
from shared.timezone import TIMEZONE
from db.get_cursor import get_cursor

# WhatsApp core
from whatsapp.core.evo_request import evo_request_with_retries
from whatsapp.core.core import _phone_number
from whatsapp.whatsapp_group.core.compute_spread_times import compute_spread_times

# Job and listener
from job_and_listener.job.core.create.create_job import create_job
from job_and_listener.job.models.job_model import JobMetadata, JobAction, JobSchedule, Job
from api.base_models import ParticipantItem, SendMassMessagesRequestModel
from job_and_listener.job_batch.core import create_job_batch
from whatsapp.mass_messages.db import insert_to_mass_messages_sql


SEND_MASS_MESSAGES_BATCH_ID = "send_mass_messages_batch"
   
# --- Define callbacks ---
def mark_message_success_in_sql(cur, recipient_id: str):
    """
    Marks a message as successfully sent in the mass_messages table.
    """
    cur.execute(
        text("UPDATE mass_messages SET success = TRUE WHERE recipient_id = :recipient_id"),
        {"recipient_id": recipient_id}
    )


def mark_message_failure_in_sql(cur, recipient_id: str, reason: str):
    """
    Marks a message as failed in the mass_messages table and records the failure reason.
    """
    cur.execute(
        text("""
            UPDATE mass_messages
            SET success = FALSE, fail_reason = :reason
            WHERE recipient_id = :recipient_id
        """),
        {"recipient_id": recipient_id, "reason": reason}
    )
   
   
   
   
def mass_messages_job(job_name, run_args, use_logging=True):
    """
    Job that sends a WhatsApp message and records success/failure in the database.

    Args:
        job_name: APScheduler job name (not used here, but passed by scheduler)
        run_args: dict containing:
            - "message": the text to send
            - "recipient_phone_number": recipient phone number
            - "recipient_id" : recipient id 
            
    """
    with get_cursor() as cur:
        
        logging.debug if use_logging else print
        
        try:
            # Send the message via the API
            resp = evo_request_with_retries(
                "message/sendText",
                {
                    "number": _phone_number(run_args["recipient_phone_number"]),
                    "text": run_args["message"],
                    "delay": 50000,  # some delay required by API
                },
            )
            # If the response is not OK, raise an exception
            if not resp.ok: 
                raise Exception(f"HTTP {resp.status_code}: {resp.text}")

            mark_message_success_in_sql(cur, run_args["recipient_id"])
            
        except Exception as e:
            
            mark_message_failure_in_sql(cur, run_args["recipient_id"], str(e))

            

    
def get_mass_message_jobs(
    participants: List[ParticipantItem],
    message: str,
    name: str,
    batch_id: str,
    *,
    start: datetime | None = None,
    min_diff: timedelta = timedelta(minutes=1, seconds=30),
) :
    """
    Create Job objects for sending mass messages.
    Only the job_id and run_args vary per number; everything else is shared.
    """

    # Default start: 30 seconds from now in configured timezone.
    if start is None:
        start = datetime.now(tz=TIMEZONE) + timedelta(seconds=30)
        
    run_times = compute_spread_times(start, min_diff=min_diff, runs=len(participants))
    
            
    job_specifics = [ { "job_id" : f"send_message_to_{p.phone_number}_{name}", "recipient_phone_number" : p.phone_number,
                       "recipient_id" : p.id, "run_time" : run_time }
                     for p, run_time in zip(participants, run_times) ] 
                   
    jobs =  [
             Job(
            metadata=JobMetadata(
                id=specific["job_id"],
                description="",
                batch_id=batch_id,
            ),
            action=JobAction(
                func=mass_messages_job,
                run_args={"message" : message, "recipient_phone_number" : specific["recipient_phone_number"],
                          "recipient_id" : specific["recipient_id"]  }
            ),
            schedule=JobSchedule(
                run_time=specific["run_time"],
                coalesce=True,
                misfire_grace_time=1,
            )
             ) for specific in job_specifics
             ]

    return jobs




        
        

def send_mass_messages_core(sched, cur, req: SendMassMessagesRequestModel):
    # Generate batch ID
    batch_id = f"{SEND_MASS_MESSAGES_BATCH_ID}/{req.name}/{datetime.now(tz=TIMEZONE).strftime('%Y%m%d_%H%M%S')}" 

    # Create batch in DB
    create_job_batch(batch_id, cur)
    
    

    # Create jobs
    jobs = get_mass_message_jobs(
        req.participants,
        req.message,
        req.name,
        batch_id=batch_id
    )
    
    #Create jobs 
    for job in jobs:
        create_job(cur, sched, job)
        
    mass_messages_tb_participants = [ {"participantItem" : participant, 
                    "job_id" : job.metadata.id} for participant, job in zip(req.participants, jobs) ]
    

    # Insert participants with job references
    insert_to_mass_messages_sql(cur, batch_id, mass_messages_tb_participants)

    



