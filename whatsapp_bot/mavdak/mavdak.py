from datetime import datetime, time
from zoneinfo import ZoneInfo

from models import MavdakRequestModel

from .mavdak_start import mavdak_start
from .mavdak_end import mavdak_end
from timezone import TIMEZONE
from apscheduler.schedulers.background import BackgroundScheduler


TIME_TO_SEND_MORNING_MESSAGES = time(8, 45)  # Time to send morning messages on the day of mavdak
TIME_TO_SEND_MORNING_MESSAGES = time(20, 58)  # Time to send morning messages on the day of mavdak


def mavdak_full_sequence(req: MavdakRequestModel, sched : BackgroundScheduler) -> None:

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

    
    dir = f"mavdaks/{req.base_date}" 

    # Step 1 — Start the mavdak
    mavdak_group_id = mavdak_start( req ,sched, dir) 


    when_to_send = datetime.combine(req.base_date, TIME_TO_SEND_MORNING_MESSAGES, tzinfo=ZoneInfo(TIMEZONE))
    # Step 2 — Schedule the morning messages
    mavdak_end(mavdak_group_id, when_to_send, sched, dir)
    
    return {}





# if __name__ == "__main__":
    
#     from datetime import date, datetime
#     from setup import setup_scheduler

    
#     mavdak_full_sequence(
#         MavdakRequestModel(
#             base_date=date.fromisoformat("2025-10-09"),
#             deadline_mavdak_list=datetime.fromisoformat("2025-10-15T17:00:00+03:00"),
#             forms_link="https://example.com/forms",
#             iluzei_reaionot_mador_mavdak="Some descriptive text here",
#             group_participants=["972532237008"]
#         ),
        
#         sched=setup_scheduler()
        
#     )