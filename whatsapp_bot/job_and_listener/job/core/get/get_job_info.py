
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Any, Dict, Optional
from datetime import datetime

from whatsapp_bot.core.domain_errors import CantRetrieveSchedulerJobError
from sqlalchemy import text


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




