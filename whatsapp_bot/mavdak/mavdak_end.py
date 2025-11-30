from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from timezone import TIMEZONE
from job_and_listener.job.core import JobToCreate, create_job, JobMetadata, JobAction, JobSchedule
from job_and_listener.job.base_job_classes.base_job_subclasses.mavdak_end_job import MavdakEndJob


def mavdak_end(mavdak_group_id: str, when_to_send: datetime, sched: BackgroundScheduler, job_batch_name : str, cur) -> None:
    """
    Schedule the sending of mavdak end messages at the given time,
    then shut down the scheduler immediately after.
    """

    metadata = JobMetadata(
        id=f"{job_batch_name}/mavdak_end",
        description="Send mavdak end messages",
        batch_id=job_batch_name,
    )
    action = JobAction(
        func=MavdakEndJob.job,
        other_args={"mavdak_group_id": mavdak_group_id},
    )
    schedule = JobSchedule(run_time=when_to_send)

    job = JobToCreate(metadata=metadata, action=action, schedule=schedule)
    create_job(cur, sched, job)
    
    print(f"Scheduled messages for {when_to_send}")