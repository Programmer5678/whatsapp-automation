from contextlib import contextmanager
from datetime import datetime
import json
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from job_status import JOBSTATUS
from exception_to_json import exception_to_json



connection_prefix = 'postgresql+psycopg://codya:030103@localhost:5432/'

connection_main = connection_prefix + 'main'
# connection_apischeduler = connection_prefix + 'lsd'
connection_apischeduler = connection_main











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
    JobEvent,
    JobSubmissionEvent,
    JobExecutionEvent
)

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
    lines = []
    lines.append(f"Event: {EVENT_NAMES.get(event.code, event.code)}")

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
































def check_deleted_status(job_id, event_code, use_logging=True):
    """Check if the job is DELETED and raise an exception if event is not JOB_REMOVED."""
    log = logging.debug if use_logging else print
    
    with get_cursor() as cur:
        current_status = cur.execute(
            text("SELECT status FROM job_information WHERE id = :job_id"),
            {"job_id": job_id}
        ).first()
        
        if current_status:
            current_status = current_status[0]
            if current_status == JOBSTATUS["DELETED"] and event_code != EVENT_JOB_REMOVED:
                log(f"Cannot update job {job_id} because it is DELETED and the event is not JOB_REMOVED.")
                raise Exception(f"Cannot update job {job_id} because it is DELETED and the event is not JOB_REMOVED.")
        else:
            log(f"Job {job_id} not found in the database.")
            return None  # Return None to indicate job wasn't found
    
    return current_status


def determine_new_status(job_id, event_code, current_status, use_logging=True):
    """Determine the new status based on the event code."""
    log = logging.debug if use_logging else print

    if event_code == EVENT_JOB_SUBMITTED:
        if current_status == JOBSTATUS["PENDING"]:
            return JOBSTATUS["RUNNING"]
        else:
            log(f"Job {job_id} is not in PENDING state, no update needed.")
            return None  # Don't update if not PENDING

    elif event_code == EVENT_JOB_EXECUTED:
        return JOBSTATUS["SUCCESS"]

    elif event_code == EVENT_JOB_ERROR:
        return JOBSTATUS["FAILURE"]
    
    elif event_code == EVENT_JOB_MISSED:
        return JOBSTATUS["MISSED"]

    else:
        log(f"Unknown event code: {event_code}. Ignoring event for job {job_id}.")
        return None  # Ignore other events


def update_job_status_in_db(job_id, status, use_logging=True):
    """Log and update the job status in the database."""
    log = logging.debug if use_logging else print

    log(f"Updating job {job_id} status to {status} in DB")

    with get_cursor() as cur:
        cur.execute(
            text("UPDATE job_information SET status = :status WHERE id = :job_id"),
            {"status": status, "job_id": job_id}
        )



# e is a serialized exception
def add_exception_to_job_sql(cur, job_name, e):
    """
    Add an issue to a job in the job_information table.

    Args:
        cur: SQLAlchemy connection or cursor
        job_name: ID or name of the job
        issue: Python object representing the issue (will be JSON-serialized)
    """
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
    
    if hasattr(event, "job_id") is False:
        return  # Ignore events without job_id
    
    job_id = event.job_id

    # Check if job is DELETED and raise an exception if event is not JOB_REMOVED
    current_status = check_deleted_status(job_id, event.code)
    if current_status is None:
        return  # Exit if job wasn't found or is DELETED with incorrect event

    # Determine the new status based on the event code
    status = determine_new_status(job_id, event.code, current_status)
    if status is None:
        return  # Exit if no status update is needed
    
    if status == JOBSTATUS["FAILURE"]:
        
        with get_cursor() as cur:
            add_exception_to_job_sql( cur, event.job_id, exception_to_json(event.exception) )

    # Update the job status in the database
    update_job_status_in_db(job_id, status)
    
    
    
    
    
    
    







def setup_scheduler(use_logging: bool = True) -> BackgroundScheduler:


    log = logging.debug if use_logging else print

    jobstores = {
        'default': SQLAlchemyJobStore(url=connection_apischeduler)
    }

    scheduler = BackgroundScheduler(jobstores=jobstores)
    


    scheduler.add_listener(
        listener
    )
    
    # with get_cursor() as cur:
    #     print("hi")
    #     print(cur.execute(text("SELECT * FROM job_information")).fetchall())
        
    # scheduler.add_listener(lambda event: print(pretty_event(event)))
    
    scheduler.start()
    return scheduler







engine = create_engine(connection_main)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# Dependency for FastAPI
@contextmanager
def get_cursor():
    cur = SessionLocal()
    try:
        yield cur
    finally:
        cur.commit()
        cur.close()
        
def get_cursor_dep():
    with get_cursor() as cur:
        yield cur
        
def create_tables():
    
    from sqlalchemy_models import GroupInfo, Participants, MassMessages, JobBatch, JobInformation  # import your models

    # Only create these two tables
    GroupInfo.__table__.create(bind=engine, checkfirst=True)
    Participants.__table__.create(bind=engine, checkfirst=True)
    MassMessages.__table__.create(bind=engine, checkfirst=True)
    JobBatch.__table__.create(bind=engine, checkfirst=True)
    JobInformation.__table__.create(bind=engine, checkfirst=True)




import logging

logging.basicConfig(
    filename='app.log',        # path to your log file
    level=logging.DEBUG,       # minimum level to record
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logging.getLogger('apscheduler').setLevel(logging.DEBUG)
