
from typing import List, Optional, Dict, Any
from apscheduler.schedulers.background import BackgroundScheduler
from job_and_listener.job.core.get.get_job_info import get_job_info
from sqlalchemy import text


def job_id_matches_prefix(job_id: Optional[str], dir_prefix: str) -> bool:
    """Returns True if the job_id matches the prefix."""
    return bool(job_id) and job_id.startswith(dir_prefix)


def get_jobs_matching_prefix(all_job_ids: List, dir_prefix: str, cur, scheduler: BackgroundScheduler) -> List[dict]:
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
        if not job_id_matches_prefix(job_id, dir_prefix):
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
    
    matching_jobs = get_jobs_matching_prefix(all_job_ids, dir_prefix, cur, scheduler)
    
    return {
        "dir_prefix": dir_prefix,
        "count": len(matching_jobs),
        "jobs": matching_jobs,
    }












