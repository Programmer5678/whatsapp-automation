#This router is for routes that test if the API and other functions like jobs are working correctly,
# Or if whatsapp connection is valid, etc.

from fastapi import APIRouter, Depends
from sqlalchemy import text
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from api.dependencies import get_cursor_dep
from job_and_listener.job.core import JobToCreate, create_job, JobMetadata, JobAction, JobSchedule
from job_and_listener.job.base_job_classes.base_job_subclasses.error_helloworld_job import ErrorHelloworldJob
from timezone import TIMEZONE
from connection import validate_whatsapp_connection, is_whatsapp_connected
from api.dependencies import get_scheduler
from job_and_listener.job.base_job_classes.base_job_subclasses.helloworld_job import HelloworldJob


test_router = APIRouter()


@test_router.get("/test_api_works")
def test_api_works():
    return "works in general"


@test_router.get("/test_sql_alchemy_cur")
def test_sql_alchemy_cur(cur = Depends(get_cursor_dep)):
    res = cur.execute(text("select 1"))
    return {"should_be_one": res.first()[0]}


@test_router.post("/schedule_error_job")
def schedule_error_job(
    cur = Depends(get_cursor_dep),
    scheduler = Depends(get_scheduler)
):
    job_id = "error_job_1"
    run_date = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=20)

    metadata = JobMetadata(
        id=job_id,
        description="Job that raises 'Hello world' exception",
        batch_id="example_batch_name",
    )
    action = JobAction(func=ErrorHelloworldJob.job, other_args={})
    schedule = JobSchedule(run_time=run_date, misfire_grace_time=1)
    job = JobToCreate(metadata=metadata, action=action, schedule=schedule)
    create_job(cur, scheduler, job)

    return {"status": "scheduled", "job_id": job_id, "run_date": run_date}




@test_router.get("/validate_whatsapp_connection")
def validate_whatsapp_connection_route():
    validate_whatsapp_connection()
    return {"message": "validated"}


@test_router.get("/is_connected")
def is_connected_route():
    return {"connected": is_whatsapp_connected()}

@test_router.post("/schedule_helloworld")
def schedule_helloworld(
                            cur = Depends(get_cursor_dep),
                            scheduler = Depends(get_scheduler)
                        ):
    job_id = "helloworld_job_1"
    run_date = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=20)
    description = "Write Hello world to helloworld.txt"
    batch_id = "example_batch_name"  # assume 1 for example
    
    metadata = JobMetadata(id=job_id, description=description, batch_id=batch_id)
    action = JobAction(func=HelloworldJob.job, other_args={})
    schedule = JobSchedule(run_time=run_date, misfire_grace_time=1)
    job = JobToCreate(metadata=metadata, action=action, schedule=schedule)
    create_job(cur, scheduler, job)

    return {"status": "scheduled", "job_id": job_id, "run_date": run_date}