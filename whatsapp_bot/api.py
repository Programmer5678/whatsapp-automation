from datetime import datetime
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from models import MavdakRequestModel, Raf0RequestModel
from mavdak.mavdak import mavdak_full_sequence
from connection import is_whatsapp_connected, validate_whatsapp_connection
from setup import setup_scheduler
from raf0 import raf0




scheduler = setup_scheduler()

app = FastAPI()


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

@app.get("/get_all_jobs")
def get_all_jobs():
    jobs = scheduler.get_jobs()
    return {
        "count": len(jobs),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            }
            for job in jobs
        ]
    }
    

@app.get("/get_all_jobs_in_dir")
def get_all_jobs_in_dir(dir_prefix: str):
    """
    Return all jobs whose IDs start with the given directory prefix.
    Example:
        /get_all_jobs_in_dir?dir_prefix=dir1/19-05-23
    """
    # Ensure the prefix ends with '/'
    if not dir_prefix.endswith('/'):
        dir_prefix += '/'
        
    print(f"Searching for jobs with prefix: {dir_prefix}")

    all_jobs = scheduler.get_jobs()
    matching_jobs = [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        }
        for job in all_jobs
        if job.id and job.id.startswith(dir_prefix)
    ]

    return {
        "dir_prefix": dir_prefix,
        "count": len(matching_jobs),
        "jobs": matching_jobs
    }



# POST endpoint
@app.post("/mavdak", status_code=status.HTTP_201_CREATED)
def create_mavdak(payload: MavdakRequestModel):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()
    

    mavdak_full_sequence(payload, scheduler)

    return {}

# Minimal API endpoint
@app.post("raf0", status_code=status.HTTP_201_CREATED)
def create_raf0(req: Raf0RequestModel):
    
    # Validate WhatsApp connection 
    validate_whatsapp_connection()
    
    raf0(req.raf0_date)
    
    return {}
    
@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down scheduler...")
    scheduler.shutdown()
    


