from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from timezone import TIMEZONE
from send_stuff_to_group import send_stuff, send_stuff2
from classes import JobInfo, WhatsappGroupCreate
from evolution_framework import _phone_number
from evo_request import evo_request
from handle_failed_adds import handle_failed_adds

def pretty_print_trigger(trigger):
    """
    Nicely print details of a CronTrigger.
    """
    print("=== CronTrigger Info ===")
    print(f" Timezone:    {trigger.timezone}")
    print(f" Start date:  {trigger.start_date}")
    print(f" End date:    {trigger.end_date}")

    print(" Schedule:")
    for field in trigger.fields:
        # Combine all expressions into a string
        expr_str = ','.join(str(e) for e in field.expressions)
        if expr_str != "*":
            print(f"   {field.name:<12} → {expr_str}")
    print("=========================\n")


def func():
    with open("log.txt", "a") as f:
        f.write(f"Hello, World! at {datetime.now()}\n")
    print(f"Hello, World! at {datetime.now()}")




# --- STEP 1: Create group (now accepts WhatsappGroupCreate) ---
def create_group(req: WhatsappGroupCreate, description: str = "") -> str:
    """
    Create group with Evolution API v2.
    Returns the group ID.
    """
    payload = {
        "subject": req.name,
        "description": description,
        "participants": [_phone_number(p) for p in req.participants],
    }

    resp = evo_request("group/create", payload)
    return resp.get("id")


def schedule_pre_deadline_job(job_info: JobInfo, deadline: datetime):
    """
    Schedule pre-deadline job: every 4h from 08:00–20:00 until the day before deadline
    """
    # compute the day before the deadline
    day_before_deadline = (deadline - timedelta(days=1)).date()
    end_of_day_before_deadline = datetime.combine(
        day_before_deadline, datetime.max.time()
    ).replace(tzinfo=ZoneInfo(TIMEZONE))

    # define the cron trigger
    trigger = CronTrigger(
        hour='8-20/4',
        start_date=datetime.now(ZoneInfo(TIMEZONE)),
        end_date=end_of_day_before_deadline,
        timezone=ZoneInfo(TIMEZONE),
    )

    # print for debugging
    pretty_print_trigger(trigger)

    # schedule the job
    job_info.scheduler.add_job(
        job_info.function,
        trigger=trigger,
        id=f"{job_info.dir}/pre_deadline_job",
        kwargs=job_info.params,
        coalesce=True,
        misfire_grace_time=600,
    )


def schedule_deadline_day_job(job_info: JobInfo, deadline: datetime):
    """
    Schedule deadline day job: every 2h from 08:00–20:00 on the deadline day
    """
    # compute start of deadline day
    start_of_deadline_day = datetime.combine(deadline.date(), datetime.min.time()).replace(
        tzinfo=ZoneInfo(TIMEZONE)
    )

    # define the cron trigger
    trigger = CronTrigger(
        hour='8-20/2',
        start_date=start_of_deadline_day,
        end_date=deadline,
        timezone=ZoneInfo(TIMEZONE),
    )
    
    # # DEBUG
    # # Debug trigger: every 2 minutes
    # trigger = CronTrigger(
    #     minute='*/2',  # every 2 minutes
    #     start_date=datetime.now(ZoneInfo(TIMEZONE)),
    #     end_date=deadline,
    #     timezone=ZoneInfo(TIMEZONE),
    # )


    # print for debugging
    pretty_print_trigger(trigger)

    # schedule the job
    job_info.scheduler.add_job(
        job_info.function,
        trigger=trigger,
        id=f"{job_info.dir}/deadline_day_job",
        kwargs=job_info.params,
        coalesce=True,
        misfire_grace_time=600,
    )

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




def job(req: WhatsappGroupCreate, group_id: str, media, messages):
    
    handle_failed_adds(req, group_id)
    send_stuff2(req, group_id)

    

def schedule_deadline_jobs(req: WhatsappGroupCreate, group_id: str) -> None:
    """
    Main function to schedule both pre-deadline and deadline-day jobs.
    """
    validate_deadline(req.deadline)  # check before scheduling


    # Create JobInfo instances for pre-deadline and deadline-day jobs
    job = JobInfo(
        scheduler=req.sched,
        function=job,
        params={"req": req, "group_id": group_id},
        dir = req.dir
    )

    # Schedule the jobs
    schedule_pre_deadline_job(job, req.deadline)
    schedule_deadline_day_job(job, req.deadline)
    
    
    
# --- FULL FLOW (now accepts WhatsappGroupCreate) ---
def create_group_and_invite(req: WhatsappGroupCreate, description: str = "") -> str:
    group_id = create_group(req, description)
    if not group_id:
        raise RuntimeError("Failed to create group or no group ID returned")

    send_stuff(req.media , req.messages, group_id)

    # input("Press Enter to continue to handle failed adds...")
    
    # schedule_deadline_jobs( lambda : handle_failed_adds(req, group_id) ,  req.deadline, req.sched )
    
    schedule_deadline_jobs( req, group_id )
    
    return group_id