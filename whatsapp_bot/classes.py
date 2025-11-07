from dataclasses import dataclass, field
import logging
from typing import List, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from datetime import datetime
from typing import Any, Optional, Dict
from sqlalchemy import text

from job_status import JOBSTATUS

# --- Simple container you asked for ---
@dataclass
class WhatsappGroupCreate:
    messages: List[str]
    name: str
    participants: List[str]
    invite_msg_title: str
    media: List[str]
    deadline: datetime
    sched :  BackgroundScheduler
    dir: str = ""  # which dir for jobs (e.g mavdaks/30.07 etc)



@dataclass
class JobInfo:
    scheduler: BackgroundScheduler
    function: Callable
    params: dict = field(default_factory=dict)  # default to empty dict if not provided
    dir : str = ""  # which dir for jobs (e.g mavdaks/30.07 etc)
    
    
    



class CreateJob:
    """
    Minimal constructor-based creator:
      - calls scheduler.add_job(...) first (so apscheduler_jobs row exists)
      - then inserts into job_information using the provided DB-API cursor
    Notes:
      - `cur` is a DB-API cursor (psycopg2 cursor style: %s placeholders)
      - commit/rollback is the caller's responsibility
      - `id` is required and used as both job id and job_information.id
    """

    def __init__(
        self,
        cur,                     # DB-API cursor (caller provides)
        scheduler,               # running APScheduler scheduler
        id: str,                 # required id (used for DB row and scheduler job id)
        description: str,
        batch_id: int,
        run_time: datetime,
        func,                    # callable to schedule
        params: Optional[Dict[str, Any]] = None,
        coalesce: bool = True,
        misfire_grace_time: int = 600,
    ):
        params = params or {}
        

        # 1) schedule APScheduler date job with id
        scheduler.add_job(
            func,
            "date",
            run_date=run_time,
            id=id,
            kwargs=params  ,
            coalesce=coalesce,
            misfire_grace_time=misfire_grace_time,
        )

        # 2) insert row into job_information (FK to apscheduler_jobs.id must now succeed)
        insert_sql = text("""
            INSERT INTO job_information (id, description, job_id, batch_id, created_at)
            VALUES (:id, :description, :job_id, :batch_id, now())
        """)

        cur.execute(
            insert_sql,
            {
                "id": id,
                "description": description,
                "job_id": id,
                "batch_id": batch_id,
            },
        )
       
       
    @classmethod 
    def delete_job(cls, scheduler: BackgroundScheduler, cur, job_id: str):
        """
        Deletes a scheduled job from both the scheduler and the database.
        
        Parameters:
            scheduler (BackgroundScheduler): The scheduler instance.
            cur: The database cursor.
            job_id (str): The ID of the job to delete.
        """
        
        log = logging.debug if False else print
        
        
        # Check if the job exists in the scheduler
        job = scheduler.get_job(job_id)
        
        if job:  # Job exists
            log("Job found in scheduler.")
            # Remove job from scheduler
            scheduler.remove_job(job_id)
            log(f"Job {job_id} removed from scheduler.")
            
            
        
        DELETED_JOB_STATUS = JOBSTATUS["DELETED"]
        
        # Remove job information from database
        delete_sql = text(f"UPDATE job_information SET status = '{DELETED_JOB_STATUS}' WHERE id = :job_id")
        cur.execute(delete_sql, {"job_id": job_id})
        

        
        
        