from typing import List
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from timezone import TIMEZONE
from send_stuff_to_group import send_stuff
from classes import JobInfo, WhatsappGroupCreate
from evolution_framework import _phone_number
from evo_request import evo_request, evo_request_with_retries
from handle_failed_adds import handle_failed_adds
from setup import setup_scheduler
from domain_errors import EvolutionServerError
from warnings import warn
import time

from sqlalchemy import text

from setup import get_cursor

import logging

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








# --- STEP 1: Create group (now accepts WhatsappGroupCreate) ---
def create_group(req: WhatsappGroupCreate) -> str:
    """
    Create group with Evolution API v2.
    Returns the group ID.
    """
    
    first_participants_to_add = req.participants[:50]
    rest_of_participants = req.participants[50:]
    
    payload = {
        "subject": req.name,
        "description": "",
        "participants": [_phone_number(p) for p in first_participants_to_add],
    }
    

    group_id = evo_request_with_retries("group/create", payload).json() ["id"]
    
    
    # # DEBUG
    # input("waiting")
    rest_of_participants = req.participants[1:]
    

    def get_batch():
        
        for i in range(0, len(rest_of_participants), 20 ):
            yield rest_of_participants[ i : i + 20 ]
    
        
    for batch in get_batch():
        
        payload = {
            "action": "add",
            "participants": [_phone_number(p) for p in batch]  # no extra brackets
        }
        
        resp = evo_request_with_retries("group/updateParticipant", payload, params={"groupJid": group_id}) 
        
        if resp.status_code == 400:
            warn(f"⚠️ Warning: Bad request for group {group_id} — {resp.text}")
        else:
            resp.raise_for_status()

        time.sleep(5)
        
            
    return group_id


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
#     job_info.scheduler.add_job(
#         job_info.function,
#         trigger=trigger,
#         id=f"{job_info.dir}/deadline_day_job",
#         kwargs=job_info.params,
#         coalesce=True,
#         misfire_grace_time=600,
#     )

def validate_deadline(deadline: datetime, min_minutes_ahead: int = 5):
    """
    Validates that the deadline is at least `min_minutes_ahead` minutes in the future.
    
    Args:
        deadline: The datetime to validate.
        min_minutes_ahead: Minimum required minutes ahead of current time.
    
    Raises:
        ValueError: If the deadline is too close or in the past.
    """
    tz = ZoneInfo(TIMEZONE)
    now = datetime.now(tz)
    min_delta = timedelta(minutes=min_minutes_ahead)

    if deadline <= now + min_delta:
        raise ValueError(
            f"❌ Invalid deadline: must be at least {min_delta} in the future.\n"
            f"Current time: {now}\nDeadline: {deadline}"
        )




def job_function_core( invite_msg_title: str, media, messages, group_id: str, cur):
    
    participants = list(cur.execute(text("select phone_number from participants where group_id = :gid"), {"gid" : group_id} ).fetchall())
    
    handle_failed_adds(participants,  invite_msg_title, group_id)
    send_stuff(media, messages, group_id)
    
def job_function( invite_msg_title: str, media, messages, group_id: str ):
    
    with get_cursor() as cur:
        job_function_core( invite_msg_title, media, messages, group_id, cur )
























def compute_spread_times(start: datetime, deadline: datetime, runs: int = 3) -> List[datetime]:
    """
    Compute `runs` datetimes evenly spaced between `start` (inclusive) and `deadline` (exclusive).
    """
    interval = (deadline - start) / runs
    return [(start + interval * i).astimezone(start.tzinfo) for i in range(runs)]


def schedule_times_as_date_jobs(job_info: JobInfo, run_times: List[datetime], base_id: str = "pre_deadline_job"):
    """
    Schedule given datetimes as one-shot 'date' jobs.
    """
    for idx, run_time in enumerate(run_times):
        job_id = f"{job_info.dir}/{base_id}_{idx}"
        print(f"Scheduling {job_id} -> {run_time.isoformat()}")

        job_info.scheduler.add_job(
            job_info.function,
            "date",
            run_date=run_time,
            id=job_id,
            kwargs=job_info.params,
            coalesce=True,
            misfire_grace_time=600,
        )


def schedule_deadline_jobs(req: WhatsappGroupCreate, group_id: str, runs: int = 3) -> None:
    """
    Schedule `runs` jobs evenly between start (now + 5 min) and the deadline.
    """
    validate_deadline(req.deadline)

    start = datetime.now(ZoneInfo(TIMEZONE)) + timedelta(minutes=5)
    deadline = req.deadline.astimezone(ZoneInfo(TIMEZONE))

    job = JobInfo(
        scheduler=req.sched,
        function=job_function,
        params={
            "invite_msg_title": req.invite_msg_title,
            "media": req.media,
            "messages": req.messages,
            "group_id": group_id,
        },
        dir=req.dir,
    )

    run_times = compute_spread_times(start, deadline, runs)
    schedule_times_as_date_jobs(job, run_times, base_id="pre_deadline_job")


def test_compute_spread_times():
    # --- Example test with timezone ---
    start = datetime(2026, 10, 30, 15, 0, tzinfo=ZoneInfo(TIMEZONE))
    deadline = datetime(2026, 10, 30, 18, 0, tzinfo=ZoneInfo(TIMEZONE))
    runs = 3

    times = compute_spread_times(start, deadline, runs)

    print("Scheduled times:")
    for i, t in enumerate(times, 1):
        print(f"{i}. {t.strftime('%H:%M')}")

    # --- Assertions ---
    expected_hours = [15, 16, 17]  # the whole hours we expect
    assert len(times) == runs, f"Expected {runs} times, got {len(times)}"
    for t, expected_hour in zip(times, expected_hours):
        assert t.hour == expected_hour, f"Expected hour {expected_hour}, got {t.hour}"
        assert t.minute == 0, f"Expected minute 0, got {t.minute}"

test_compute_spread_times()        
    




    
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
#         dir=req.dir
#     )

#     # Schedule the jobs
#     schedule_pre_deadline_job(job, req.deadline)
#     schedule_deadline_day_job(job, req.deadline)
    
    























    
    

# --- FULL FLOW (now accepts WhatsappGroupCreate) ---
def create_group_and_invite(cur, req: WhatsappGroupCreate) -> str:
    group_id = create_group(req)
    if not group_id:
        raise RuntimeError("Failed to create group or no group ID returned")
    
    # Insert into group_info
    cur.execute(
        text("INSERT INTO group_info (group_id) VALUES (:gid)"),
        {"gid": group_id},
    )

    # Insert participants
    for phone_number in req.participants:
        cur.execute(
            text(
                "INSERT INTO participants (phone_number, group_id) VALUES (:phone_number, :gid)"
            ),
            {"gid": group_id, "phone_number": phone_number},
        )




    job_function_core(
        invite_msg_title=req.invite_msg_title,
        media=req.media,
        messages=req.messages,
        group_id=group_id, 
        cur=cur
    )
    
    
    schedule_deadline_jobs( req, group_id )
    
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
#     dir="/blah"
# )


# with get_cursor() as cur:
#     create_group_and_invite( cur, whatsapp_group )