"""
Service layer for job operations.

The service functions implement business logic and return fully-formed JSON
responses so that API endpoints can remain thin one-liners.
"""

from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from job.core import (
    del_job,
    get_job_info as core_get_job_info,
    get_jobs_in_dir as core_get_jobs_in_dir,
)

# --- Public service functions used by the router ---


def delete_job_service(job_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Service to delete a single job. Returns the standard response dict.
    """
    del_job(job_id, cur, scheduler)
    return {"message": f"Job {job_id} deleted."}


def delete_job_batch_service(batch_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Deletes all jobs in a batch, removes the batch from the DB and returns info about deleted jobs.
    """
    job_ids = [row[0] for row in cur.execute(
        text("SELECT id FROM job_information WHERE batch_id = :batch_id"),
        {"batch_id": batch_id}
    ).fetchall()]

    deleted_jobs_info = []
    for job_id in job_ids:
        del_job(job_id, cur, scheduler)
        deleted_jobs_info.append(core_get_job_info(job_id, cur, scheduler))

    cur.execute(
        text("DELETE FROM job_batch WHERE name = :batch_id"),
        {"batch_id": batch_id}
    )

    return {"message": f"All jobs in batch {batch_id} deleted.", "deleted_jobs_info": deleted_jobs_info}


def delete_and_recreate_job_batch_service(batch_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Deletes a batch and recreates it in the DB. Returns details about deleted jobs.
    """
    deleted_info = delete_job_batch_service(batch_id, cur, scheduler)

    # recreate batch row
    cur.execute(
        text("INSERT INTO job_batch (name) VALUES (:batch_id)"),
        {"batch_id": batch_id}
    )

    return {"message": f"Batch {batch_id} deleted and recreated.", "deleted_jobs_info": deleted_info.get("deleted_jobs_info")}


def get_job_info_service(job_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Returns job info or a not-found message payload.
    """
    job_info = core_get_job_info(job_id, cur, scheduler)
    if job_info is None:
        return {"message": f"Job {job_id} not found.", "job": None}
    return {"job": job_info}


def get_all_jobs_service(cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Returns all jobs across directories.
    """
    return get_all_jobs_in_dir_service("", cur, scheduler)


def get_all_jobs_in_dir_service(dir_prefix: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Return list of jobs whose IDs start with dir_prefix (if given).
    """
    return core_get_jobs_in_dir(dir_prefix, cur, scheduler)
