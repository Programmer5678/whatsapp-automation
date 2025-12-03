from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from whatsapp_bot.core.timezone import TIMEZONE
from whatsapp_bot.whatsapp.whatsapp_group.features.mavdak.mavdak_end.mavdak_end_job import MavdakEndJobFunc
from job_and_listener.job.models.job_to_create_model import JobAction, JobMetadata, JobSchedule, JobToCreate
from job_and_listener.job.core.create.create_job import create_job

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
        func=MavdakEndJobFunc.job,
        run_args={"mavdak_group_id": mavdak_group_id},
    )
    schedule = JobSchedule(run_time=when_to_send)

    job = JobToCreate(metadata=metadata, action=action, schedule=schedule)
    create_job(cur, sched, job)
    
    print(f"Scheduled messages for {when_to_send}")