from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from job_and_listener.job.models.job_model import Job, JobMetadata
from typing import Callable, Any





def add_date_job(
    scheduler: BackgroundScheduler,
    func: Callable,
    run_date: Any,
    *args,
    **kwargs,
) -> None:
    """
    Add a job to the APScheduler that only uses a run_date (DateTrigger).

    ⚠️ Important: This wrapper enforces that only 'date' jobs are scheduled.
    This is because the job_information table and scheduler state assume that
    all jobs in the scheduler are pending jobs, and the system does not
    support tracking cron or interval jobs. Adding non-date triggers
    can break consistency.

    Args:
        scheduler: The APScheduler scheduler instance.
        func: The callable to run.
        run_date: The exact datetime when the job should run.
        *args: Positional arguments for func.
        **kwargs: Keyword arguments for func and scheduler settings like:
                  - id
                  - coalesce
                  - misfire_grace_time
                  etc.
    """
    scheduler.add_job(
        func,
        trigger="date",  # enforce DateTrigger only
        run_date=run_date,
        *args,
        **kwargs,
    )


def schedule_job(scheduler: BackgroundScheduler, job: "Job") -> None:
    """
    Schedule a Job object using APScheduler.
    """
    add_date_job(
        scheduler=scheduler,
        func=job.action.func,
        run_date=job.schedule.run_time,
        id=job.metadata.id,
        kwargs={
            "job_name": job.metadata.id,
            "run_args": job.action.run_args,
        },
        coalesce=job.schedule.coalesce,
        misfire_grace_time=job.schedule.misfire_grace_time,
    )



def insert_job_row(cur, metadata: JobMetadata) -> None:
    """
    Insert a row in the job_information table.
    """
    insert_sql = text("""
        INSERT INTO job_information (id, description, job_id, batch_id, created_at)
        VALUES (:id, :description, :job_id, :batch_id, now())
    """)
    cur.execute(
        insert_sql,
        {
            "id": metadata.id,
            "description": metadata.description,
            "job_id": metadata.id,
            "batch_id": metadata.batch_id,
        },
    )


def create_job(cur, scheduler: BackgroundScheduler, job: Job) -> None:
    """
    High-level helper that schedules a job and creates its DB row.
    """
    schedule_job(scheduler, job)
    insert_job_row(cur, job.metadata)
            