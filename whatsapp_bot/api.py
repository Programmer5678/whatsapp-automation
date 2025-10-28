from datetime import datetime
from fastapi import Depends, FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from models import ChangeParticipantsRequestModel, GetParticipantsRequestModel, HakhanaRequestModel, MavdakRequestModel, Raf0RequestModel
from mavdak.mavdak import mavdak_full_sequence
from connection import is_whatsapp_connected, validate_whatsapp_connection
from setup import get_cursor_dep, setup_scheduler, create_tables
from raf0 import raf0
from typing import Dict, Any, Optional
from sqlalchemy import text

from hakhana import hakhana
from dynamic_group_changes import change_participants
from evo_request import evo_request_with_retries
from evolution_framework import _phone_number


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








    


@app.get("/one")
def example_endpoint():
    validate_whatsapp_connection()
    return {"message": "Hello, World!"}



@app.get("/is_connected")
def is_connected():
    
    connected = is_whatsapp_connected()
    return {"connected": connected}



@app.delete("/delete_all_jobs")
def delete_all_jobs():
    
    scheduler.remove_all_jobs()
    return {"message": "All jobs deleted."}


    
    
    
    
def _format_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    try:
        return dt.isoformat()
    except Exception:
        # Fallback: str()
        return str(dt)


def get_jobs_in_dir(dir_prefix: str) -> Dict[str, Any]:
    """
    Return information about jobs whose IDs start with the given directory prefix.
    If dir_prefix is an empty string, returns all jobs.

    Ensures that when a non-empty prefix is provided it ends with a '/'.
    Also extracts trigger.start_date and trigger.end_date when available.
    """
    # Normalize prefix
    if dir_prefix and not dir_prefix.endswith('/'):
        dir_prefix = dir_prefix + '/'

    all_jobs = scheduler.get_jobs()

    def matches(job_id: Optional[str]) -> bool:

        return bool(job_id) and job_id.startswith(dir_prefix)

    matching_jobs = []
    for job in all_jobs:
        if not matches(job.id):
            continue

        # Safely extract start_date and end_date from the trigger if present
        trigger = job.trigger
        start_date = getattr(trigger, 'start_date', None)
        end_date = getattr(trigger, 'end_date', None)

        job_dict = {
            "id": job.id,
            "name": job.name,
            "next_run_time": _format_dt(job.next_run_time) if getattr(job, 'next_run_time', None) else None,
            "trigger": str(trigger),
            "start_date": _format_dt(start_date),
            "end_date": _format_dt(end_date),
        }
        matching_jobs.append(job_dict)

    return {
        "dir_prefix": dir_prefix,
        "count": len(matching_jobs),
        "jobs": matching_jobs,
    }


@app.get("/get_all_jobs")
def get_all_jobs():
    # Return all jobs by calling the shared helper with an empty prefix
    return get_jobs_in_dir("")


@app.get("/get_all_jobs_in_dir")
def get_all_jobs_in_dir(dir_prefix: str):
    # Delegate to shared helper
    return get_jobs_in_dir(dir_prefix)


@app.post("/get_participants")
def get_participants(req : GetParticipantsRequestModel):
    
    all_participants_resp = evo_request_with_retries(method = "/group/participants", get=True, params={"groupJid" : req.gid})
    all_numbers_id = [ p["phoneNumber"] for p in all_participants_resp.json()["participants"] ]
    all_numbers  = [ _phone_number(p) for p in all_numbers_id ]
    
    all_numbers_without_excluded = [ n for n in all_numbers if not n in req.participants_to_exclude]
    excluded_that_not_in_group = [ n for n in req.participants_to_exclude if not n in all_numbers]
    
    return { "all_numbers_without_excluded" : all_numbers_without_excluded, "excluded_that_not_in_group" : excluded_that_not_in_group, "all_numbers" : all_numbers}
    
    
    
    
    



# POST endpoint
@app.post("/mavdak", status_code=status.HTTP_201_CREATED)
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
    


