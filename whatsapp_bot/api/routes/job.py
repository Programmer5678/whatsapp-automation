"""
This file contains API routes for managing jobs in the WhatsApp bot application.
It provides endpoints to delete jobs, retrieve job information, and manage job batches.
Jobs are handled using APScheduler and job metadata is stored in another SQL database
"""

from fastapi import APIRouter, Depends, status
from apscheduler.schedulers.background import BackgroundScheduler

from api.dependencies import get_cursor_dep
from api.dependencies import get_scheduler

from job_and_listener.job.service import (
    delete_job_service,
    delete_job_batch_service,
    delete_and_recreate_job_batch_service,
    get_job_info_service,
    get_all_jobs_service,
    get_all_jobs_in_dir_service,
)

job_router = APIRouter(prefix="/job")


@job_router.delete("/delete_job", status_code=status.HTTP_200_OK)
def delete_job_endpoint(job_id: str, cur = Depends(get_cursor_dep), scheduler: BackgroundScheduler = Depends(get_scheduler)):
    """
    Delete a single job by ID from both the scheduler and DB.
    """
    return delete_job_service(job_id, cur, scheduler)


@job_router.delete("/delete_job_batch", status_code=status.HTTP_200_OK)
def delete_job_batch_endpoint(batch_id: str, cur = Depends(get_cursor_dep), scheduler: BackgroundScheduler = Depends(get_scheduler)):
    """
    Delete all jobs in a batch and remove the batch from the DB.
    """
    return delete_job_batch_service(batch_id, cur, scheduler)


@job_router.post("/delete_and_recreate_job_batch", status_code=status.HTTP_200_OK)
def delete_and_recreate_job_batch_endpoint(batch_id: str, cur = Depends(get_cursor_dep), scheduler: BackgroundScheduler = Depends(get_scheduler)):
    """
    Delete a batch of jobs and then recreate the batch in the DB.
    """
    return delete_and_recreate_job_batch_service(batch_id, cur, scheduler)


@job_router.get("/get_job_info", status_code=status.HTTP_200_OK)
def get_job_info_endpoint(job_id: str, cur = Depends(get_cursor_dep), scheduler: BackgroundScheduler = Depends(get_scheduler)):
    """
    Retrieve job information by ID from both DB and APScheduler.
    """
    return get_job_info_service(job_id, cur, scheduler)


@job_router.get("/get_all_jobs", status_code=status.HTTP_200_OK)
def get_all_jobs_endpoint(cur = Depends(get_cursor_dep), scheduler: BackgroundScheduler = Depends(get_scheduler)):
    """
    Retrieve all jobs across all directories.
    """
    return get_all_jobs_service(cur, scheduler)


@job_router.get("/get_all_jobs_in_dir", status_code=status.HTTP_200_OK)
def get_all_jobs_in_dir_endpoint(dir_prefix: str, cur = Depends(get_cursor_dep), scheduler: BackgroundScheduler = Depends(get_scheduler)):
    """
    Retrieve all jobs matching a specific directory prefix.
    """
    return get_all_jobs_in_dir_service(dir_prefix, cur, scheduler)



















