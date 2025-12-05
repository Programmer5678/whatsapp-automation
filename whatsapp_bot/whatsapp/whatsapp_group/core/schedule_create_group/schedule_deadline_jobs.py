

from zoneinfo import ZoneInfo

from shared.timezone import TIMEZONE
from whatsapp.whatsapp_group.models.job_funcs.new_group_job_func.new_group import NewGroupJobFunc
from whatsapp.whatsapp_group.models.whatsapp_group_create import WhatsappGroupCreate

from datetime import datetime, timedelta

from job_and_listener.job.core.create.create_job import create_job
from job_and_listener.job.models.job_model import JobAction, JobMetadata, JobSchedule, Job
from whatsapp.whatsapp_group.core.compute_spread_times import compute_spread_times

def get_job_metadatas(description, batch_id, num_jobs):
    
    return [ JobMetadata(id=f"{batch_id}/pre_deadline_job/{idx}" , description=description, batch_id=batch_id)  for idx in range(num_jobs)]

def get_job_actions(func, run_args, num_jobs):
    return [
        JobAction(
            func=func,
            run_args=run_args,
        )
        
        for _ in range(num_jobs)
    ]
    



def schedule_deadline_jobs(cur, req: WhatsappGroupCreate, group_id: str, runs: int = 3, minutes_before_start=1 ) -> None:
    """
    Schedule `runs` jobs evenly between start (now + 5 min) and the deadline.
    """

    start = datetime.now(ZoneInfo(TIMEZONE)) + timedelta(minutes=minutes_before_start)
    deadline = req.deadline.astimezone(ZoneInfo(TIMEZONE))



    metadatas = get_job_metadatas(description="Send messages to group, and attempt to add participants(send them link)"
                                  , batch_id=req.job_batch_name
                                  , num_jobs = runs)
    
    actions = get_job_actions(
        func=NewGroupJobFunc.job,
        run_args={
            "invite_msg_title": req.invite_msg_title,
            "media": req.media,
            "messages": req.messages,
            "group_id": group_id,
        },
        num_jobs=runs,
    )

    
    run_times = compute_spread_times(start, deadline=deadline, min_diff=timedelta(minutes=1), runs=runs)
    schedules = [ JobSchedule(run_time=run_time) for run_time in run_times]
    
    jobs = [ Job(metadata=metadata, action=action, schedule=schedule) for metadata,action, schedule in zip(metadatas, actions, schedules) ]
    
    for j in jobs:
        create_job(cur, req.sched, j)
    
