from datetime import date, datetime
from typing import List, Any
from pydantic import BaseModel, Field, constr
from apscheduler.schedulers.background import BackgroundScheduler
from classes import WhatsappGroupCreate
from schedule_create_group import create_group_and_invite
from models import HakhanaRequestModel


def hakhana(req: HakhanaRequestModel, sched: BackgroundScheduler) -> None:
    """
    Create a simple 'hakhana' group.
    - No media or custom messages.
    - invite_msg_title: "בבקשה להיכנס לקבוצה של ההכנה לקצונה שתתקיים ב {date}"
    - group_name: "הכנה לקצונה תקשוב {date}"
    - dir: "hakhana/{date}"
    """
    group_name = f"הכנה לקצונה תקשוב {req.date}"
    invite_msg_title = f"בבקשה להיכנס לקבוצה של ההכנה לקצונה שתתקיים ב {req.date}"

    hakhana_group = WhatsappGroupCreate(
        name=group_name,
        participants=req.group_participants,
        messages=[],               # no messages
        invite_msg_title=invite_msg_title,
        media=[],                  # no media
        sched=sched,
        deadline=req.deadline,     # passed directly
        dir=f"hakhana/{req.date}"
    )

    group_id = create_group_and_invite(hakhana_group)
    print(f"{group_name} group ID: {group_id}")
    return
