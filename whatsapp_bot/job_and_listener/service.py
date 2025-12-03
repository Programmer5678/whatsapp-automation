# jobs/services/delete.py

from typing import Any, Dict
from job_and_listener.job.core.delete.core import delete_job
from apscheduler.schedulers.background import BackgroundScheduler
from job_and_listener.job.core.get.core import get_jobs_in_dir
from job_and_listener.job_batch.core import delete_job_batch
from job_and_listener.job.core.get.get_job_info import get_job_info
from sqlalchemy import text


def delete_job_service(job_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    deleted = delete_job(job_id, cur, scheduler)
    if deleted:
        return {"message": f"Job {job_id} removed from scheduler."}
    else:
        return {"message": f"Job {job_id} not in pending (either doesn't exist or is already running)."}


def delete_job_batch_service(batch_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    deleted_job_ids = delete_job_batch(batch_id, cur, scheduler)
    deleted_jobs_info = [get_job_info(job_id, cur, scheduler) for job_id in deleted_job_ids]

    return {
        "message": f"All jobs in batch {batch_id} deleted.",
        "deleted_jobs_info": deleted_jobs_info
    }


def delete_and_recreate_job_batch_service(batch_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    deleted_info = delete_job_batch_service(batch_id, cur, scheduler)
    cur.execute(
        text("INSERT INTO job_batch (name) VALUES (:batch_id)"),
        {"batch_id": batch_id}
    )
    return {
        "message": f"Batch {batch_id} deleted and recreated.",
        "deleted_jobs_info": deleted_info.get("deleted_jobs_info")
    }



def get_job_info_service(job_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Returns job info or a not-found message payload.
    """
    job_info = get_job_info(job_id, cur, scheduler)
    if job_info is None:
        return {"message": f"Job {job_id} not found.", "job": None}
    return {"job": job_info}


def get_all_jobs_in_dir_service(dir_prefix: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Return list of jobs whose IDs start with dir_prefix (if given).
    """
    return get_jobs_in_dir(dir_prefix, cur, scheduler)

def get_all_jobs_service(cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Returns all jobs across directories.
    """
    return get_all_jobs_in_dir_service("", cur, scheduler)