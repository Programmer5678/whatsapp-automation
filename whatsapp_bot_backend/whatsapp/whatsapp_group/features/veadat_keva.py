
from whatsapp.whatsapp_group.core.schedule_create_group.core import create_group_and_invite
from whatsapp.whatsapp_group.models.whatsapp_group_create import WhatsappGroupCreate


from typing import Any, List
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import date

from job_and_listener.job_batch.core import create_job_batch
from api.base_models import VeadatKevaRequestModel

def veadat_keva(
    req: VeadatKevaRequestModel,
    sched: BackgroundScheduler,
    cur: Any,
) -> str:
    """
    Create a 'veadat keva' group and invite participants.

    Expects `req` to hold:
      - req.date (date)
      - req.deadline (datetime)
      - req.group_participants (List[str] / validated phone numbers)

    Returns:
        The created group_id (string).
    """
    # derive values from req
    veadat_keva_date = req.date
    veadat_keva_deadline = req.deadline
    veadat_keva_time = (
        veadat_keva_deadline.time().strftime("%H:%M")
        if hasattr(veadat_keva_deadline, "time")
        else ""
    )

    job_batch_name = f"veadat_keva/{veadat_keva_date}"
    create_job_batch(job_batch_name, cur)

    group_invite_msg_title = (
        f"בבקשה להצטרף לקבוצה של ועדת הקבע שתתקיים ב {veadat_keva_date}"
    )

    group_messages = [
        f"""שלום לכולם,
לקראת הקקצ יתקיימו ראיונות בראשות רען מפקדים. הראיונות בויסי (יישלח אליכם לינק סמוך לשעת הראיון).
בבקשה - כולם למלא את הטופס הבא שמטרתו לוודא מאיזה יוזר אתם מתחברים.
{veadat_keva_date} שעה {veadat_keva_time} מתחילים
"""
    ]

    group_name = f"ועדת קבע {veadat_keva_date}"

    veadat_group = WhatsappGroupCreate(
        name=group_name,
        participants=req.group_participants,
        messages=group_messages,
        invite_msg_title=group_invite_msg_title,
        media=[],  # no media unless you want to attach
        sched=sched,
        deadline=veadat_keva_deadline,
        job_batch_name=job_batch_name,
    )

    group_id = create_group_and_invite(cur, veadat_group)
    print(f"{group_name} group ID: {group_id}")
    return group_id