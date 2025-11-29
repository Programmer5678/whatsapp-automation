import json
import logging
from apscheduler.events import (
    EVENT_SCHEDULER_STARTED,
    EVENT_SCHEDULER_SHUTDOWN,
    EVENT_SCHEDULER_PAUSED,
    EVENT_SCHEDULER_RESUMED,
    EVENT_EXECUTOR_ADDED,
    EVENT_EXECUTOR_REMOVED,
    EVENT_JOBSTORE_ADDED,
    EVENT_JOBSTORE_REMOVED,
    EVENT_JOB_ADDED,
    EVENT_JOB_REMOVED,
    EVENT_JOB_MODIFIED,
    EVENT_JOB_SUBMITTED,
    EVENT_JOB_MAX_INSTANCES,
    EVENT_JOB_EXECUTED,
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED,
    JobExecutionEvent
)
from sqlalchemy import text

from job_status import JOBSTATUS
from exception_to_json import exception_to_json
from db.get_cursor import get_cursor


EVENT_NAMES = {
    EVENT_SCHEDULER_STARTED: "SCHEDULER_STARTED",
    EVENT_SCHEDULER_SHUTDOWN: "SCHEDULER_SHUTDOWN",
    EVENT_SCHEDULER_PAUSED: "SCHEDULER_PAUSED",
    EVENT_SCHEDULER_RESUMED: "SCHEDULER_RESUMED",
    EVENT_EXECUTOR_ADDED: "EXECUTOR_ADDED",
    EVENT_EXECUTOR_REMOVED: "EXECUTOR_REMOVED",
    EVENT_JOBSTORE_ADDED: "JOBSTORE_ADDED",
    EVENT_JOBSTORE_REMOVED: "JOBSTORE_REMOVED",
    EVENT_JOB_ADDED: "JOB_ADDED",
    EVENT_JOB_REMOVED: "JOB_REMOVED",
    EVENT_JOB_MODIFIED: "JOB_MODIFIED",
    EVENT_JOB_SUBMITTED: "JOB_SUBMITTED",
    EVENT_JOB_MAX_INSTANCES: "JOB_MAX_INSTANCES",
    EVENT_JOB_EXECUTED: "JOB_EXECUTED",
    EVENT_JOB_ERROR: "JOB_ERROR",
    EVENT_JOB_MISSED: "JOB_MISSED",
}


def pretty_event(event):
    lines = [f"Event: {EVENT_NAMES.get(event.code, event.code)}"]

    if hasattr(event, "job_id"):
        lines.append(f"job_id={event.job_id}")

    if hasattr(event, "scheduled_run_time"):
        lines.append(f"scheduled_run_time={event.scheduled_run_time}")

    if isinstance(event, JobExecutionEvent):
        if event.exception:
            lines.append(f"exception={event.exception}")
        else:
            lines.append(f"retval={event.retval}")

    return "\n".join(lines)


def get_job_status(job_id, use_logging=True):
    """
    Retrieve the current status of a job from the database.

    Returns:
        str: Current job status
        None: If the job does not exist
    """
    log = logging.debug if use_logging else print

    with get_cursor() as cur:
        result = cur.execute(
            text("SELECT status FROM job_information WHERE id = :job_id"),
            {"job_id": job_id}
        ).first()

        if not result:
            log(f"Job {job_id} not found in the database.")
            return None

        return result[0]


def ensure_status_isnt_deleted(job_id, job_status, use_logging=True):
    """
    Ensure that the given event code is compatible with the job's current status.

    Raises an exception if the event is incompatible.
    Currently enforces that DELETED jobs can only receive JOB_REMOVED events.
    """
    log = logging.debug if use_logging else print

    if job_status == JOBSTATUS["DELETED"] :
        raise Exception(f"Cannot update job {job_id}: DELETED jobs shouldnt be recieving events as they dont exist in apscheduler.")



def determine_new_status(job_id, event_code, current_status, use_logging=True):
    """
    Determine the new status of a job based on the incoming event code and its current status.

    Returns:
        str: The new job status if a change is needed.
        None: If no status update is needed given the current status and event code.

    Behavior:
    - EVENT_JOB_SUBMITTED: Changes status from PENDING → RUNNING.  
      If the job is not currently PENDING, returns None to avoid race conditions
      where an event arrives after the status has already progressed (e.g., PENDING → something → RUNNING).
    - EVENT_JOB_EXECUTED: Sets status to SUCCESS.
    - EVENT_JOB_ERROR: Sets status to FAILURE.
    - EVENT_JOB_MISSED: Sets status to MISSED.
    - pending events can also be removed - set to DELETED on remove 
    - Any other event codes: Returns None and logs.

    This function ensures that job status transitions occur safely and only when appropriate,
    preventing inconsistent or out-of-order state changes.
    """
    log = logging.debug if use_logging else print
    
    # log(f"HOLA HOLA event_code {event_code}, job_id {job_id} .") #DEBUG

    if event_code == EVENT_JOB_SUBMITTED:
        if current_status == JOBSTATUS["PENDING"]:
            return JOBSTATUS["RUNNING"]
        else:
            log(f"Job {job_id} is not in PENDING state, no update needed.")
            return None

    elif event_code == EVENT_JOB_EXECUTED:
        return JOBSTATUS["SUCCESS"]

    elif event_code == EVENT_JOB_ERROR:
        log(f"Job {job_id} encountered an error.")
        return JOBSTATUS["FAILURE"]
    
    elif event_code == EVENT_JOB_MISSED:
        return JOBSTATUS["MISSED"]
    
    elif event_code == EVENT_JOB_REMOVED and current_status == JOBSTATUS["PENDING"] : # Can only delete pending job. # WATCH OUT - RACE CONDITIONS
        return JOBSTATUS["DELETED"]
        

    else:
        log(f"Unknown event code: {event_code}. Ignoring event for job {job_id}.")
        return None



def update_job_status_in_db(job_id, status, use_logging=True):
    log = logging.debug if use_logging else print
    log(f"Updating job {job_id} status to {status} in DB")

    with get_cursor() as cur:
        cur.execute(
            text("UPDATE job_information SET status = :status WHERE id = :job_id"),
            {"status": status, "job_id": job_id}
        )


def add_exception_to_job_sql(cur, job_name, e):
    cur.execute(
        text("""
            UPDATE job_information
            SET exception = :exception_json
            WHERE id = :job_name
        """),
        {
            "exception_json": json.dumps(e),
            "job_name": job_name
        }
    )


def listener(event):
    if not hasattr(event, "job_id"):
        return
    
    job_id = event.job_id
    current_status = get_job_status(job_id)
    ensure_status_isnt_deleted( job_id, current_status )

    if current_status is None:  # If job doesnt exist - return 
        return

    new_status = determine_new_status(job_id, event.code, current_status)
    if new_status is None:  # No change needed - return None
        return
    
    
    if new_status == JOBSTATUS["FAILURE"]:
        with get_cursor() as cur:
            add_exception_to_job_sql(cur, job_id, exception_to_json(event.exception))

    update_job_status_in_db(job_id, new_status)
