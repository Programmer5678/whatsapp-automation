from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import Depends, FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from models import ChangeParticipantsRequestModel, GetParticipantsRequestModel, HakhanaRequestModel, MavdakRequestModel, Raf0RequestModel, SendMassMessagesRequestModel
from mavdak.mavdak import mavdak_full_sequence
from connection import is_whatsapp_connected, validate_whatsapp_connection
from setup import get_cursor, get_cursor_dep, setup_scheduler, create_tables
from raf0 import raf0
from typing import Dict, Any, List, Optional
from sqlalchemy import text, bindparam

from hakhana import hakhana
from dynamic_group_changes import change_participants
from evo_request import evo_request_with_retries
from evolution_framework import _phone_number
from mass_messanger import MassMessenger


create_tables()
scheduler = setup_scheduler()

app = FastAPI()



@app.get("/test")
def test():
    return "works in general"

@app.get("/test_sql_alchemy")
def test_sql_alchemy( cur = Depends(get_cursor_dep) ):
    res = cur.execute(text("select 1"))
    return { "should_be_one" : res.first()[0] }




from fastapi import FastAPI, Depends
from datetime import datetime, timedelta
from classes import CreateJob
from timezone import TIMEZONE
    

    
def write_helloworld():
    
    
    
    
    print("waiting...")
    import time
    time.sleep(10)
    print("done waiting")
    
    # from warnings import warn
    # warn("Trying warn inside write_helloworld")
    
    print("Writing Hello world to helloworld.txt")
    with open("helloworld.txt", "w") as f:
        f.write("Hello world")
        
    # raise Exception("Job failed")
    
    
    
    
    
@app.post("/schedule_helloworld")
def schedule_helloworld(cur=Depends(get_cursor_dep)):
    job_id = "helloworld_job_1"
    run_date = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=20)
    description = "Write Hello world to helloworld.txt"
    batch_id = "example_batch_name"  # assume 1 for example
    



    CreateJob(
        cur=cur,
        scheduler=scheduler,
        id=job_id,
        func=write_helloworld,
        params={},
        run_time=run_date,
        description=description,
        batch_id=batch_id,
        misfire_grace_time=1
    )
    return {"status": "scheduled", "job_id": job_id, "run_date": run_date}




def add_issue_to_job_sql(cur, job_name, issue):
    
    """
    Add an issue to a job in the job_information table.

    Args:
        cur: SQLAlchemy connection or cursor
        job_name: ID or name of the job
        issue: Python object representing the issue (will be JSON-serialized)
    """
    import json
    cur.execute(
        text("""
            UPDATE job_information
            SET issues =  array_append( issues, :issue_json )
            WHERE id = :job_name
        """),
        {
            "issue_json": json.dumps(issue),
            "job_name": job_name
        }
    )

def raise_helloworld_exception():
    
    
    with get_cursor() as cur:
        add_issue_to_job_sql(cur, "error_job_1", {"info": "Issue 1"})
        add_issue_to_job_sql(cur, "error_job_1", {"info": "Issue 2"})
    
    raise Exception("Hello world exception from scheduled job")

@app.post("/schedule_error_job")
def schedule_error_job(cur=Depends(get_cursor_dep)):
    job_id = "error_job_1"
    run_date = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=20)
    description = "Job that raises 'Hello world' exception"
    batch_id = "example_batch_name"  # example batch

    # Schedule the job
    CreateJob(
        cur=cur,
        scheduler=scheduler,
        id=job_id,
        func=raise_helloworld_exception,
        run_time=run_date,
        description=description,
        batch_id=batch_id,
        misfire_grace_time=1
    )

    return {"status": "scheduled", "job_id": job_id, "run_date": run_date}







@app.get("/one")
def example_endpoint():
    validate_whatsapp_connection()
    return {"message": "Hello, World!"}



@app.get("/is_connected")
def is_connected():
    
    connected = is_whatsapp_connected()
    return {"connected": connected}


def del_job(job_id: str, cur):
    # Delete job from scheduler and update DB
    CreateJob.delete_job(scheduler, cur, job_id)

@app.delete("/delete_job")
def delete_job(job_id: str, cur=Depends(get_cursor_dep)):
    
    # Delete job from scheduler and update DB
    del_job(job_id, cur)
    
    
    
    return {"message": f"Job {job_id} deleted."}


@app.delete("/delete_job_batch")
def delete_job_batch(batch_id: str, cur=Depends(get_cursor_dep)):
    
    # Query for all job IDs with the given batch_id
    job_ids = [ row[0] for row in cur.execute(
        text("SELECT id FROM job_information WHERE batch_id = :batch_id"),
        {"batch_id": batch_id}
    ).fetchall() ]
    
    deleted_jobs_info = []
    
    # Delete each job
    for job_id in job_ids:
        del_job(job_id, cur)
        
        deleted_jobs_info.append( get_job_info(job_id, cur, scheduler) )
        
    cur.execute(
        text("DELETE FROM job_batch WHERE name = :batch_id"),
        {"batch_id": batch_id}
    )
    
    return {"message": f"All jobs in batch {batch_id} deleted.", "deleted_jobs_info": deleted_jobs_info}



    
    
def _format_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        # Fallback: str()
        return str(dt)



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
    job = scheduler.get_job(job_id)
    if job:
        # APScheduler job info (just add these specific fields to job_info)
        trigger = job.trigger
        start_date = getattr(trigger, 'start_date', None)
        end_date = getattr(trigger, 'end_date', None)

        job_info.update({
            "next_run_time": _format_dt(job.next_run_time) if getattr(job, 'next_run_time', None) else None,
            "trigger": str(trigger),
            "start_date": _format_dt(start_date),
            "end_date": _format_dt(end_date),
        })
    
    return job_info


def matches(job_id: Optional[str], dir_prefix: str) -> bool:
    """Returns True if the job_id matches the prefix."""
    return bool(job_id) and job_id.startswith(dir_prefix)

def get_matching_jobs(all_job_ids: List, dir_prefix: str, cur) -> List[dict]:
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



def get_jobs_in_dir(dir_prefix: str, cur) -> Dict[str, Any]:
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
    
    matching_jobs = get_matching_jobs(all_job_ids, dir_prefix, cur)
    

    return {
        "dir_prefix": dir_prefix,
        "count": len(matching_jobs),
        "jobs": matching_jobs,
    }


@app.get("/get_job_info")
def get_job_info_endpoint(job_id: str, cur=Depends(get_cursor_dep)):
    return get_job_info(job_id, cur, scheduler)

@app.get("/get_all_jobs")
def get_all_jobs(cur=Depends(get_cursor_dep)):
    # Return all jobs by calling the shared helper with an empty prefix
    return get_jobs_in_dir("", cur)


@app.get("/get_all_jobs_in_dir")
def get_all_jobs_in_dir(dir_prefix: str, cur=Depends(get_cursor_dep)):
    # Delegate to shared helper
    return get_jobs_in_dir(dir_prefix, cur)


@app.post("/get_participants")
def get_participants(req : GetParticipantsRequestModel):
    
    all_participants_resp = evo_request_with_retries(method = "/group/participants", get=True, params={"groupJid" : req.gid})
    all_numbers_id = [ p["phoneNumber"] for p in all_participants_resp.json()["participants"] ]
    all_numbers  = [ _phone_number(p) for p in all_numbers_id ]
    
    all_numbers_without_excluded = [ n for n in all_numbers if not n in req.participants_to_exclude]
    excluded_that_not_in_group = [ n for n in req.participants_to_exclude if not n in all_numbers]
    
    return { "all_numbers_without_excluded" : all_numbers_without_excluded, "excluded_that_not_in_group" : excluded_that_not_in_group, "all_numbers" : all_numbers}
    
    
    
    
    
    
    
    
    
    





def calculate_relevant_participants(cur, participants):
    """
    Returns only participants whose IDs are not marked success=TRUE in mass_messages.

    Args:
        cur: Active database cursor or SQLAlchemy connection.
        participants: List of participant objects (must have 'id' attribute).

    Returns:
        List of participants still relevant for sending.
    """
    if not participants:
        return []

    ids = [p.id for p in participants]

    res = cur.execute(
        text("SELECT id FROM mass_messages WHERE id IN :ids AND success = TRUE").bindparams( bindparam("ids", expanding=True) )
        , {"ids": ids}
    ).fetchall()

    already_success_ids = {row[0] for row in res }

    return [p for p in participants if p.id not in already_success_ids]
    
    
@app.post("/sendMassMessages", status_code=status.HTTP_201_CREATED)
def send_mass_messages(payload: SendMassMessagesRequestModel, cur = Depends(get_cursor_dep)):

    validate_whatsapp_connection() 
    
    relevant_participants = calculate_relevant_participants(cur, payload.participants)

    # --- Validate uniqueness of phone numbers ---
    phones = [p.phone_number for p in relevant_participants]
    if len(phones) != len(set(phones)):
        raise ValueError("Duplicate phone numbers detected in participants.")
    

    # --- Insert participants into mass_messages table ---
    for part in relevant_participants:
        cur.execute(
            text("""INSERT INTO mass_messages (id, phone_number, success) VALUES (:id, :phone_number, :success)
                    ON CONFLICT (id) DO NOTHING
                 """),
            {"id": part.id, "phone_number": part.phone_number, "success": None}
        )
 
    # --- Define callbacks ---
    def on_success(phone_number: str):
        cur.execute(
            text("UPDATE mass_messages SET success = TRUE WHERE phone_number = :phone_number"),
            {"phone_number": phone_number}
        )
        cur.commit()

    def on_failure(phone_number: str, reason : str):
        cur.execute(
            text("UPDATE mass_messages SET success = FALSE, fail_reason = :reason WHERE phone_number = :phone_number" ),
            {"phone_number": phone_number, "reason" : reason } 
        )
        cur.commit()

    # --- Create messenger and send messages ---
    messenger = MassMessenger(
        numbers=phones,
        message=payload.message,
        on_success=on_success,
        on_failure=on_failure,
    )

    messenger.send_all()
    # no return value, status_code=201















# POST endpoint
@app.post("/mavdak", status_code=status.HTTP_202_ACCEPTED)
def create_mavdak(payload: MavdakRequestModel, cur = Depends(get_cursor_dep)  ):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()

    mavdak_full_sequence(payload, scheduler, cur)
    

    return {}

@app.post("/change_participants", status_code=status.HTTP_201_CREATED)
def change_participants_endpoint(
    req: ChangeParticipantsRequestModel,
    cur = Depends(get_cursor_dep)
):
    validate_whatsapp_connection()
    change_participants(cur, req.gid, req.participants)
    return {"message": "Participants updated successfully in DB. Will be used as source of truth next job"}

    
    
      


# Minimal API endpoint
@app.post("/raf0", status_code=status.HTTP_201_CREATED)
def create_raf0(req: Raf0RequestModel , cur = Depends(get_cursor_dep)  ):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()
    
    raf0(req, scheduler, cur)
    
    return {}
    
# Minimal API endpoint
@app.post("/hakhana", status_code=status.HTTP_201_CREATED)
def create_hakhana(req: HakhanaRequestModel, cur = Depends(get_cursor_dep)):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()
    
    hakhana(req, scheduler, cur)
    
    return {} 
    
@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down scheduler...")
    scheduler.shutdown()
    


