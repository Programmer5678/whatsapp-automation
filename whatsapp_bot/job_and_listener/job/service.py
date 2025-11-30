"""
Service layer for job operations.

The service functions implement business logic and return fully-formed JSON
responses so that API endpoints can remain thin one-liners.
"""

from typing import Dict, Any, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from job_and_listener.job.core import (
    del_job,
    get_job_info as core_get_job_info,
    get_jobs_in_dir as core_get_jobs_in_dir,
)

from db.get_cursor import get_cursor



# --- Public service functions used by the router ---

JOBSTATUS = {"DELETED" : "DELETED"} # DEBUG

def delete_job_service(job_id: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:

    """
    If a job is still in apscheduelr table - meaning it hasnt been run yet - Deletes a scheduled job from both the scheduler and marks as deleted in job_infromation
    
    Parameters:
        scheduler (BackgroundScheduler): The scheduler instance.
        cur: The database cursor or SQLAlchemy connection (for DB row removal if needed).
        job_id (str): The ID of the job to delete.
    """

    log = logging.debug if False else print

    # Check if the job exists in the scheduler
    job = scheduler.get_job(job_id)

    if job:  # Job exists
        log("Job found in scheduler.")
        # Remove job from scheduler
        scheduler.remove_job(job_id)
        with get_cursor() as cur:
            cur.execute(
                text("UPDATE job_information SET status = :status WHERE id = :job_id"),
                {"status": JOBSTATUS["DELETED"], "job_id": job_id}
            )
        return {"message" : f"Job {job_id} removed from scheduler." }
        
    else:
        return {"message" : f"Job {job_id} isnt in pending ( either doesnt exist or is already running hence outside of apscheduler table )"}


    







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
        delete_job_service(job_id, cur, scheduler)
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
