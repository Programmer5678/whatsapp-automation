"""
Core helper functions used by job services.
Contains lower-level helpers that interact with the DB and APScheduler.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text

from api.dependencies import get_cursor_dep
from domain_errors import CantRetrieveSchedulerJobError
from classes import CreateJob


def del_job(job_id: str, cur, scheduler: BackgroundScheduler):
    # Delete job from scheduler and update DB
    CreateJob.delete_job(scheduler, cur, job_id)


def _format_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        # Fallback: str()
        return str(dt)


def scheduler_get_job_with_handling(job_id: str, scheduler: BackgroundScheduler):
    try:
        job = scheduler.get_job(job_id)
    except Exception as e:
        raise CantRetrieveSchedulerJobError(
            f"Error retrieving job {job_id} from scheduler. Possibly due to serialized function being moved"
        ) from e
    return job


def get_job_info(job_id: str, cur, scheduler: BackgroundScheduler) -> Optional[Dict[str, Any]]:
    """
    Retrieves job information from both the job_information table and the APScheduler job.

    Args:
        job_id (str): The job ID to search for.
        cur: The DB cursor (to query the database).
        scheduler: The APScheduler instance.

    Returns:
        dict: A dictionary containing job information from both sources, or None if not found.
    """
    # 1) Query job_information table for the job details
    job_info_sql = text("""
        SELECT *
        FROM job_information
        WHERE id = :job_id
    """)
    
    result = cur.execute(job_info_sql, {"job_id": job_id}).first()

    if not result:
        # If no job information was found in the database, return None
        return None

    # Unpack the result from the database directly
    job_info = {**result._mapping }

    # 2) Query APScheduler for the job details
    job = scheduler_get_job_with_handling(job_id, scheduler)
    if job:
        # APScheduler job info (just add these specific fields to job_info)
        trigger = job.trigger
        start_date = getattr(trigger, 'start_date', None)
        end_date = getattr(trigger, 'end_date', None)

        job_info.update({
            "next_run_time": _format_dt(getattr(job, 'next_run_time', None)),
            "trigger": str(trigger),
            "start_date": _format_dt(start_date),
            "end_date": _format_dt(end_date),
        })
    
    return job_info


def matches(job_id: Optional[str], dir_prefix: str) -> bool:
    """Returns True if the job_id matches the prefix."""
    return bool(job_id) and job_id.startswith(dir_prefix)


def get_matching_jobs(all_job_ids: List, dir_prefix: str, cur, scheduler: BackgroundScheduler) -> List[dict]:
    """
    Returns a list of job dictionaries that match the given prefix.

    Parameters:
        - all_jobs: A list of job objects to filter.
        - dir_prefix: The prefix that job IDs should start with to be included.

    Returns:
        - A list of dictionaries containing job details for matching jobs.
    """
    matching_jobs = []

    # Loop through all jobs and filter based on the matches function
    for job_id in all_job_ids:
        if not matches(job_id, dir_prefix):
            continue
        
        # Call the get_job_info function to extract job details
        job_dict = get_job_info(job_id, cur, scheduler)
        
        # Append the result to matching_jobs
        matching_jobs.append(job_dict)

    return matching_jobs


def get_jobs_in_dir(dir_prefix: str, cur, scheduler: BackgroundScheduler) -> Dict[str, Any]:
    """
    Return information about jobs whose IDs start with the given directory prefix.
    If dir_prefix is an empty string, returns all jobs.

    Ensures that when a non-empty prefix is provided it ends with a '/'.
    Also extracts trigger.start_date and trigger.end_date when available.
    """
    # Normalize prefix
    if dir_prefix and not dir_prefix.endswith('/'):
        dir_prefix = dir_prefix + '/'

    all_job_ids = [ el[0] for el in cur.execute(text("SELECT id FROM job_information")).fetchall() ]
    
    matching_jobs = get_matching_jobs(all_job_ids, dir_prefix, cur, scheduler)
    
    return {
        "dir_prefix": dir_prefix,
        "count": len(matching_jobs),
        "jobs": matching_jobs,
    }


def delete_job_batch_service(batch_id: str, cur, scheduler: BackgroundScheduler):
    """
    Deletes all jobs in a batch and removes the batch from the DB.
    Returns info about deleted jobs.
    """
    # Get all job IDs for this batch
    job_ids = [row[0] for row in cur.execute(
        text("SELECT id FROM job_information WHERE batch_id = :batch_id"),
        {"batch_id": batch_id}
    ).fetchall()]

    deleted_jobs_info = []

    # Delete each job and collect info
    for job_id in job_ids:
        del_job(job_id, cur, scheduler)
        deleted_jobs_info.append(get_job_info(job_id, cur, scheduler))

    # Remove batch row
    cur.execute(
        text("DELETE FROM job_batch WHERE name = :batch_id"),
        {"batch_id": batch_id}
    )

    return deleted_jobs_info
