from typing import List

from zoneinfo import ZoneInfo

from whatsapp.core.core import BUSINESS_HOURS_DEFAULT, _phone_number
from whatsapp.whatsapp_group.features.participants.db import _save_group_and_participants
from whatsapp.core.evo_request import  evo_request_with_retries


from sqlalchemy import text


from datetime import datetime, timedelta

from job_and_listener.job.core.create.create_job import create_job
from job_and_listener.job.models.job_model import JobAction, JobMetadata, JobSchedule, Job
from whatsapp.whatsapp_group.models.job_funcs.add_participants_in_batches import AddParticipantsInBatchesJobFunc
from whatsapp.whatsapp_group.models.whatsapp_group_create import WhatsappGroupCreate
from shared.timezone import TIMEZONE
from whatsapp.whatsapp_group.core.schedule_create_group.schedule_deadline_jobs import schedule_deadline_jobs
from job_and_listener.job_batch.core import create_job_batch



def create_group(req: WhatsappGroupCreate, cur) -> str:
    """
    Create group with Evolution API v2.
    Returns the group ID.
    """
    first_participants_to_add = req.participants[:10]
    rest_of_participants = req.participants[10:]
    
    # rest_of_participants = req.participants # DEBUG

    payload = {
        "subject": req.name,
        "description": "",
        "participants": [_phone_number(p) for p in first_participants_to_add],
    }

    group_id = evo_request_with_retries("group/create", payload).json()["id"]

    # Add remaining participants in batches of 20
    schedule_add_participants_in_batches( group_id, rest_of_participants, req.job_batch_name, req.sched, cur)

    return group_id


# --- scheduler helper: schedule a single one-off job that runs the function once ---
def schedule_add_participants_in_batches(
    group_id: str,
    participants: List[str],
    job_batch_name,
    sched, 
    cur
) -> str:
    """
    Schedule a single one-off APScheduler job that will call add_participants_in_batches.
    - sched: an APScheduler scheduler instance (e.g., BackgroundScheduler)
    - run_date: datetime when the job should run. If None, run 1 second from now.
    - job_id: optional job id (useful if you want to refer to it later). If omitted, a generated id is returned.

    Returns the job id.
    """

    full_job_id = f"{job_batch_name}/add_participants_in_batches"

    # ensure the function is a top-level callable (it is)
    metadata = JobMetadata(
        id=full_job_id,
        description=f"Add remainding participants to group: {participants} " + group_id,
        batch_id=job_batch_name,
    )
    action = JobAction(
        func=AddParticipantsInBatchesJobFunc.job,
        run_args={
            "group_id": group_id,
            "participants": participants
        },
    )
    schedule = JobSchedule(run_time=datetime.now(TIMEZONE))
    job = Job(metadata=metadata, action=action, schedule=schedule)
    
    job = Job(metadata=metadata, action=action, schedule=schedule)
    create_job(cur, sched, job)

    return full_job_id



def validate_deadline(deadline: datetime, min_minutes_ahead: int = 5, 
                      bussiness_hours: list = BUSINESS_HOURS_DEFAULT) -> None:
    """
    Validates that the deadline is at least `min_minutes_ahead` minutes in the future
    and falls within business hours.
    
    Raises:
        ValueError: If the deadline is too close, in the past, or outside business hours.
    """
    tz = TIMEZONE
    now = datetime.now(tz)
    min_delta = timedelta(minutes=min_minutes_ahead)

    if deadline <= now + min_delta:
        raise ValueError(
            f"❌ Invalid deadline: must be at least {min_delta} in the future.\n"
            f"Current time: {now}\nDeadline: {deadline}"
        )

    weekday = deadline.weekday()  # 0 = Monday, 6 = Sunday
    start_time, end_time = bussiness_hours[weekday]

    if start_time == end_time:
        raise ValueError(
            f"❌ Invalid deadline: {deadline} is on a non-working day (closed hours)."
        )

    if not (start_time <= deadline.time() <= end_time):
        raise ValueError(
            f"❌ Invalid deadline: {deadline} is outside business hours "
            f"({start_time} - {end_time})."
        )




# --- FULL FLOW (now accepts WhatsappGroupCreate) ---
def create_group_and_invite(cur, req: WhatsappGroupCreate) -> str:
    
    validate_deadline(req.deadline)  
    
        
    group_id = create_group(req, cur)
    if not group_id:
        raise RuntimeError("Failed to create group or no group ID returned")

    # persist group and participants (extracted, but logic unchanged)
    _save_group_and_participants(cur, group_id, req.participants)

    schedule_deadline_jobs(cur, req, group_id)

    return group_id


