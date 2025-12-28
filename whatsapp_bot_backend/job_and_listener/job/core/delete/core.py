"""
Service layer for job operations.

The service functions implement business logic and return fully-formed JSON
responses so that API endpoints can remain thin one-liners.
"""

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import text


# --- Public service functions used by the router ---

JOBSTATUS = {"DELETED" : "DELETED"} # DEBUG

# jobs/delete_logic.py (or inside jobs/delete.py if you prefer)

def delete_job(job_id: str, cur, scheduler: BackgroundScheduler) -> bool:
    """
    Deletes a scheduled job from APScheduler and marks it as deleted in the DB.
    Returns True if the job existed in scheduler, False otherwise.
    """
    job = scheduler.get_job(job_id)
    if job:
        scheduler.remove_job(job_id)
        cur.execute(
            text("UPDATE job_information SET status = :status WHERE id = :job_id"),
            {"status": JOBSTATUS["DELETED"], "job_id": job_id}
        )
        return True
    return False


