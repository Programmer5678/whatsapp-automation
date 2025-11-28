import time
from typing import List

from zoneinfo import ZoneInfo

from timezone import TIMEZONE
from classes import CreateJob, JobInfo, WhatsappGroupCreate
from evolution_framework import _phone_number
from evo_request import  evo_request_with_retries
from warnings import warn


from sqlalchemy import text


import logging
from datetime import datetime, timedelta

from compute_spread_times import  BUSINESS_HOURS_DEFAULT, compute_spread_times
from base_job_classes.new_group.new_group import NewGroupJob
from base_job_classes.add_participants_in_batches import AddParticipantsInBatchesJob


def pretty_print_trigger(trigger, use_logging=True):
    """
    Nicely display details of a CronTrigger.
    Set use_logging=True to use logging.debug() instead of print().
    """
    log = logging.debug if use_logging else print

    log("=== CronTrigger Info ===")
    log(f" Timezone:    {trigger.timezone}")
    log(f" Start date:  {trigger.start_date}")
    log(f" End date:    {trigger.end_date}")

    log(" Schedule:")
    for field in trigger.fields:
        expr_str = ','.join(str(e) for e in field.expressions)
        if expr_str != "*":
            log(f"   {field.name:<12} → {expr_str}")
    log("=========================\n")







def create_group(req: WhatsappGroupCreate, cur) -> str:
    """
    Create group with Evolution API v2.
    Returns the group ID.
    """
    first_participants_to_add = req.participants[:50]
    rest_of_participants = req.participants[50:]
    
    # rest_of_participants = req.participants # DEBUG

    payload = {
        "subject": req.name,
        "description": "",
        "participants": [_phone_number(p) for p in first_participants_to_add],
    }

    group_id = evo_request_with_retries("group/create", payload).json()["id"]

    # Add remaining participants in batches of 20
    schedule_add_participants_in_batches( group_id, rest_of_participants, req.job_batch_name, req.sched, cur)

    return group_id














# --- scheduler helper: schedule a single one-off job that runs the function once ---
def schedule_add_participants_in_batches(
    group_id: str,
    participants: List[str],
    job_batch_name,
    sched, 
    cur
) -> str:
    """
    Schedule a single one-off APScheduler job that will call add_participants_in_batches.
    - sched: an APScheduler scheduler instance (e.g., BackgroundScheduler)
    - run_date: datetime when the job should run. If None, run 1 second from now.
    - job_id: optional job id (useful if you want to refer to it later). If omitted, a generated id is returned.

    Returns the job id.
    """

    full_job_id = f"{job_batch_name}/add_participants_in_batches"

    # ensure the function is a top-level callable (it is)
    job = CreateJob(
        func=AddParticipantsInBatchesJob.job,
        run_time=datetime.now(ZoneInfo(TIMEZONE)),
        other_args={
            "group_id": group_id,
            "participants": participants
        },
        id=full_job_id,
        batch_id=job_batch_name,
        scheduler=sched,
        cur=cur,
        description=f"Add remainding participants to group: {participants} " + group_id,
    )

    return full_job_id






# def schedule_pre_deadline_job(job_info: JobInfo, deadline: datetime):
#     """
#     Schedule pre-deadline job: every 4h from 08:00–20:00 until the day before deadline
#     """
#     # compute the day before the deadline
#     day_before_deadline = (deadline - timedelta(days=1)).date()
#     end_of_day_before_deadline = datetime.combine(
#         day_before_deadline, datetime.max.time()
#     ).replace(tzinfo=ZoneInfo(TIMEZONE))

#     # # define the cron trigger
#     # trigger = CronTrigger(
#     #     hour='8-20/4',
#     #     start_date=datetime.now(ZoneInfo(TIMEZONE)) + timedelta(minutes=5),
#     #     end_date=end_of_day_before_deadline,
#     #     timezone=ZoneInfo(TIMEZONE),
#     # )

#     # DEBUG
#     trigger = CronTrigger(
#         minute='*/5',  # every 2 minutes
#         start_date=datetime.now(ZoneInfo(TIMEZONE)) + timedelta(minutes=5),
#         end_date=end_of_day_before_deadline,
#         timezone=ZoneInfo(TIMEZONE),
#     )


#     # print for debugging
#     pretty_print_trigger(trigger)

#     # schedule the job
#     job_info.scheduler.add_job(
#         job_info.function,
#         trigger=trigger,
#         id=f"{job_info.dir}/pre_deadline_job",
#         kwargs=job_info.params,
#         coalesce=True,
#         misfire_grace_time=600,
#     )


# def schedule_deadline_day_job(job_info: JobInfo, deadline: datetime):
#     """
#     Schedule deadline day job: every 2h from 08:00–20:00 on the deadline day
#     """
#     # compute start of deadline day
#     start_of_deadline_day = datetime.combine(deadline.date(), datetime.min.time()).replace(
#         tzinfo=ZoneInfo(TIMEZONE)
#     )

#     # define the cron trigger
#     trigger = CronTrigger(
#         hour='8-20/2',
#         start_date=start_of_deadline_day,
#         end_date=deadline,
#         timezone=ZoneInfo(TIMEZONE),
#     )
    
#     # # DEBUG
#     # # Debug trigger: every 2 minutes
#     # trigger = CronTrigger(
#     #     minute='*/2',  # every 2 minutes
#     #     start_date=datetime.now(ZoneInfo(TIMEZONE)) + timedelta(minutes=5),
#     #     end_date=deadline,
#     #     timezone=ZoneInfo(TIMEZONE),
#     # )


#     # print for debugging
#     pretty_print_trigger(trigger)

#     # schedule the job
#     job_info.scheduler.add_job(job",
#         kwargs=job_info.params,
#         job_info.function,
#         trigger=trigger,
#         id=f"{job_info.dir}/deadline_day_
#         coalesce=True,
#         misfire_grace_time=600,
#     )




def validate_deadline(deadline: datetime, min_minutes_ahead: int = 5, bussiness_hours: list = BUSINESS_HOURS_DEFAULT) -> None:
    """
    Validates that the deadline is at least `min_minutes_ahead` minutes in the future
    and falls within business hours.
    
    Raises:
        ValueError: If the deadline is too close, in the past, or outside business hours.
    """
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    min_delta = timedelta(minutes=min_minutes_ahead)

    if deadline <= now + min_delta:
        raise ValueError(
            f"❌ Invalid deadline: must be at least {min_delta} in the future.\n"
            f"Current time: {now}\nDeadline: {deadline}"
        )

    weekday = deadline.weekday()  # 0 = Monday, 6 = Sunday
    start_time, end_time = bussiness_hours[weekday]

    if start_time == end_time:
        raise ValueError(
            f"❌ Invalid deadline: {deadline} is on a non-working day (closed hours)."
        )

    if not (start_time <= deadline.time() <= end_time):
        raise ValueError(
            f"❌ Invalid deadline: {deadline} is outside business hours "
            f"({start_time} - {end_time})."
        )









def schedule_times_as_date_jobs(cur, job_info: JobInfo, run_times: List[datetime], base_id: str = "pre_deadline_job"):
    """
    Schedule given datetimes as one-shot 'date' jobs.
    """
    
    # print(f"Scheduling {len(run_times)} jobs for {job_info.job_batch_name}...")
    
    for idx, run_time in enumerate(run_times):
        job_full_id = f"{job_info.job_batch_name}/{base_id}/{idx}"
        print(f"Scheduling {job_full_id} -> {run_time.isoformat()}")
        
        # print(f"Scheduling job {job_id} at {run_time}")
        
        CreateJob(func=job_info.function,
                  run_time=run_time,
                  id=job_full_id,
                  batch_id=job_info.job_batch_name,
                  scheduler=job_info.scheduler,
                  cur=cur,
                  description=f"Send messages to group, and attempt to add participants(send them link) at {run_time.isoformat()}",
                  other_args = job_info.params
                  )

        # job_info.scheduler.add_job(
        #     job_info.function,
        #     "date",
        #     run_date=run_time,
        #     id=job_full_id,
        #     kwargs=job_info.params,
        #     coalesce=True,
        #     misfire_grace_time=600,
        # )


def schedule_deadline_jobs(cur, req: WhatsappGroupCreate, group_id: str, runs: int = 3, minutes_before_start=1 ) -> None:
    """
    Schedule `runs` jobs evenly between start (now + 5 min) and the deadline.
    """
    validate_deadline(req.deadline)  

    start = datetime.now(ZoneInfo(TIMEZONE)) + timedelta(minutes=minutes_before_start)
    deadline = req.deadline.astimezone(ZoneInfo(TIMEZONE))


    job = JobInfo(
        scheduler=req.sched,
        function=NewGroupJob.job,
        params={
            "invite_msg_title": req.invite_msg_title,
            "media": req.media,
            "messages": req.messages,
            "group_id": group_id,
        },
        job_batch_name=req.job_batch_name,
    )

    run_times = compute_spread_times(start, deadline=deadline, min_diff=timedelta(minutes=1), runs=runs)
    schedule_times_as_date_jobs(cur, job, run_times, base_id="pre_deadline_job")







    
# def schedule_deadline_jobs(req: WhatsappGroupCreate, group_id: str) -> None:
#     """
#     Main function to schedule both pre-deadline and deadline-day jobs.
#     """
#     validate_deadline(req.deadline)  # check before scheduling


#     # Create JobInfo instances for pre-deadline and deadline-day jobs
#     job = JobInfo(
#         scheduler=req.sched,
#         function=job_function,
#         params={
#             "invite_msg_title": req.invite_msg_title,
#             "media": req.media,
#             "messages": req.messages,
#             "group_id": group_id
#         },
#         job_batch_name=req.job_batch_name
#     )

#     # Schedule the jobs
#     schedule_pre_deadline_job(job, req.deadline)
#     schedule_deadline_day_job(job, req.deadline)
    
    





def _save_group_and_participants(cur, group_id: str, participants: list[str]) -> None:
    """
    Insert group info and participants into the DB.

    Logic kept identical to the original:
    - single INSERT into group_info
    - then a simple for-loop inserting each participant one-by-one
    - same SQL and parameter names
    """
    # Insert into group_info
    cur.execute(
        text("INSERT INTO group_info (group_id) VALUES (:gid)"),
        {"gid": group_id},
    )

    # Insert participants (one-by-one, same logic as before)
    for phone_number in participants:
        cur.execute(
            text(
                "INSERT INTO participants (phone_number, group_id) VALUES (:phone_number, :gid)"
            ),
            {"gid": group_id, "phone_number": phone_number},
        )




# --- FULL FLOW (now accepts WhatsappGroupCreate) ---
def create_group_and_invite(cur, req: WhatsappGroupCreate) -> str:
    
    cur.execute(text("INSERT INTO job_batch (name) VALUES (:name)"), {"name": req.job_batch_name} )
    
    group_id = create_group(req, cur)
    if not group_id:
        raise RuntimeError("Failed to create group or no group ID returned")

    # persist group and participants (extracted, but logic unchanged)
    _save_group_and_participants(cur, group_id, req.participants)

    schedule_deadline_jobs(cur, req, group_id)

    return group_id



# whatsapp_group = WhatsappGroupCreate(
#     messages=["hi"],
#     name="alahu",
#     participants=[
#                     "972529064417"
#                   , "972544444444"  
#                   ],
#     invite_msg_title="",
#     media=[],
#     deadline=datetime(2025, 10, 26, tzinfo=ZoneInfo(TIMEZONE)),
#     sched=setup_scheduler(),
#     job_batch_name="/blah"
# )


# with get_cursor() as cur:
#     create_group_and_invite( cur, whatsapp_group )