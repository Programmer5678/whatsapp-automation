from sqlalchemy import text
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from job_and_listener.job.core.delete.core import delete_job    

def delete_job_batch(batch_id: str, cur, scheduler: BackgroundScheduler) -> List[str]:
    """
    Deletes all jobs in a batch from scheduler and marks them as deleted in DB.
    Returns a list of deleted job_ids.
    """
    job_ids = [row[0] for row in cur.execute(
        text("SELECT id FROM job_information WHERE batch_id = :batch_id"),
        {"batch_id": batch_id}
    ).fetchall()]

    deleted_jobs = []
    for job_id in job_ids:
        if delete_job(job_id, cur, scheduler):
            deleted_jobs.append(job_id)

    cur.execute(
        text("DELETE FROM job_batch WHERE name = :batch_id"),
        {"batch_id": batch_id}
    )

    return deleted_jobs


