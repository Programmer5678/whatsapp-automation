from contextlib import contextmanager
from datetime import datetime
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from job_status import JOBSTATUS



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

def setup_scheduler(use_logging: bool = True) -> BackgroundScheduler:


    log = logging.debug if use_logging else print

    jobstores = {
        'default': SQLAlchemyJobStore(url=connection_apischeduler)
    }

    scheduler = BackgroundScheduler(jobstores=jobstores)
    
    
            
    def listener(event):
        job_id = event.job_id
        if event.code == EVENT_JOB_SUBMITTED:
            status = JOBSTATUS["RUNNING"]
        elif event.code == EVENT_JOB_EXECUTED:
            status = JOBSTATUS["SUCCESS"]
        elif event.code == EVENT_JOB_ERROR:
            status = JOBSTATUS["FAILURE"]
        else:
            log(f"why here? {pretty_event(event)}")
            return  # ignore other events

        log(f"Updating job {job_id} status to {status} in DB")

        with get_cursor() as cur:
            
            cur.execute(
                text("UPDATE job_information SET status = :status WHERE id = :job_id"),
                {"status": status, "job_id": job_id}
            )
            


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
