from datetime import datetime, timedelta
import logging
from typing import Any, List
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
from api.base_models import SendMassMessagesRequestModel
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
        
        # try: #DEBUG
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

        # except Exception as e:  # Record failure in SQL
        #     # Capture full traceback and store it in DB
            
        #     # mark_message_failure_in_sql(cur, run_args["p"], "failed")
        #     # log(exception_to_json(e))
        #     mark_message_failure_in_sql(cur, run_args["p"], exception_to_json(e))
        #     raise  # Re-raise so the scheduler knows this job failed

        # If message was sent successfully, mark it as success in DB
        mark_message_success_in_sql(cur, run_args["p"])



def create_mass_message_jobs(
    numbers: List[str],
    message: str,
    name: str,
    batch_id: str,
    *,
    start: datetime | None = None,
    min_diff: timedelta = timedelta(minutes=1, seconds=30),
) -> List["Job"]:
    """
    Create Job objects for sending mass messages.
    Only the job_id and run_args vary per number; everything else is shared.
    """

    # Default start: 30 seconds from now in configured timezone.
    if start is None:
        start = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=30)

    run_times = compute_spread_times(start, min_diff=min_diff, runs=len(numbers))

    # --- 1) Prepare per-number metadata pieces (job_id + run_args) ---
    per_number_specs = []
    for p in numbers:
        job_id = f"send_message_to_{p}_{name}"
        run_args = {"message": message, "p": p}
        per_number_specs.append((job_id, run_args))

    # --- 2) Build Job objects using a list comprehension ---
    jobs = [
        Job(
            metadata=JobMetadata(
                id=job_id,
                description="",
                batch_id=batch_id,
            ),
            action=JobAction(
                func=mass_messages_job,
                run_args=run_args,
            ),
            schedule=JobSchedule(
                run_time=run_time,
                coalesce=True,
                misfire_grace_time=1,
            ),
        )
        for (job_id, run_args), run_time in zip(per_number_specs, run_times)
    ]

    return jobs



def schedule_jobs(
    scheduler: Any,
    cur: Any,
    jobs: List["Job"],
) -> None:
    """
    Persist and schedule a list of Job objects with APScheduler / DB.

    Args:
        scheduler: APScheduler instance
        cur: DB cursor/connection
        jobs: list of Job objects created by create_mass_message_jobs
    """
    for job in jobs:
        create_job(cur, scheduler, job)
        
        
        









def papapair(
    cur, participants, batch_id: str, job_list: list["Job"]
):
    """
    Inserts participants into mass_messages table with the corresponding job_info_id.
    Assumes participants and job_list are in the same order.

    Args:
        cur: DB cursor
        participants: list of participant objects with 'id' and 'phone_number'
        batch_id: the batch ID for this insert
        job_list: list of Job objects corresponding to participants
    """
    insert_sql = text("""
        INSERT INTO mass_messages (
            batch_id, recipient_id, recipient_phone_number, job_info_id
        ) VALUES (
            :batch_id, :recipient_id, :recipient_phone_number, :job_info_id
        )
    """)

    for participant, job in zip(participants, job_list):
        cur.execute(
            insert_sql,
            {
                "batch_id": batch_id,
                "recipient_id": participant.id,
                "recipient_phone_number": participant.phone_number,
                "job_info_id": job.metadata.id,
            }
        )        

def send_mass_messages_core(sched, cur, req: SendMassMessagesRequestModel):
    # Generate batch ID
    batch_id = f"{SEND_MASS_MESSAGES_BATCH_ID}/{req.name}/{datetime.now(tz=ZoneInfo(TIMEZONE)).strftime('%Y%m%d_%H%M%S')}" 

    # Create batch in DB
    create_job_batch(batch_id, cur)

    # Extract phone numbers
    phone_numbers = [p.phone_number for p in req.participants]

    # Create jobs
    job_list = create_mass_message_jobs(
        phone_numbers,
        req.message,
        req.name,
        batch_id=batch_id
    )
    
    # Schedule the jobs
    schedule_jobs(sched, cur, job_list)

    # Insert participants with job references
    papapair(cur, req.participants, batch_id, job_list)

    

