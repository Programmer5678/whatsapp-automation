from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text
from job_and_listener.job.models.job_to_create_model import JobToCreate, JobMetadata


def schedule_job(scheduler: BackgroundScheduler, job: JobToCreate) -> None:
    """
    Schedule a job with APScheduler.
    """
    scheduler.add_job(
        job.action.func,
        "date",
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


def create_job(cur, scheduler: BackgroundScheduler, job: JobToCreate) -> None:
    """
    High-level helper that schedules a job and creates its DB row.
    """
    schedule_job(scheduler, job)
    insert_job_row(cur, job.metadata)
            