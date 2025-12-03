from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from models import MavdakRequestModel

from .mavdak_start import mavdak_start
from .mavdak_end.mavdak_end import mavdak_end
from whatsapp_bot.core.timezone import TIMEZONE
from apscheduler.schedulers.background import BackgroundScheduler


TIME_TO_SEND_MORNING_MESSAGES = time(8, 45)  # Time to send morning messages on the day of mavdak
# TIME_TO_SEND_MORNING_MESSAGES = time(20, 58)  # Time to send morning messages on the day of mavdak


def mavdak_full_sequence(req: MavdakRequestModel, sched : BackgroundScheduler, cur) -> None:

    """
    Schedules a full mavdak workflow:
    1. Starts mavdak group creation and setup.
    2. Schedules end messages at the morning of mavdak day.

    Args:
        base_date: The date of the mavdak itself (usually a Sunday).
        deadline_mavdak_list: The deadline for finalizing and sending the list (usually Wednesday 16:00).
        forms_link: URL for the form participants should fill.
        iluzei_reaionot_mador_mavdak: Additional notes or instructions from the instructor.
        group_participants: List of participant phone numbers in international format.
    """

    
    job_batch_name = f"mavdaks/{req.base_date}" 

    # Step 1 — Start the mavdak
    mavdak_group_id = mavdak_start( req ,sched, job_batch_name, cur) 
    

    when_to_send = datetime.combine(req.base_date, TIME_TO_SEND_MORNING_MESSAGES, tzinfo=ZoneInfo(TIMEZONE))
    # when_to_send = datetime.now(tz=ZoneInfo(TIMEZONE)) + timedelta(seconds=20)  # DEBUG
    
    # Step 2 — Schedule the morning messages
    mavdak_end(mavdak_group_id, when_to_send, sched, job_batch_name, cur)
    
    return {}





# if __name__ == "__main__":
    
