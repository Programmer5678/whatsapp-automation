from apscheduler.schedulers.background import BackgroundScheduler
from whatsapp.whatsapp_group.models.whatsapp_group_create import WhatsappGroupCreate
from whatsapp.whatsapp_group.core.schedule_create_group.core import create_group_and_invite
from api.base_models import HakhanaRequestModel
from job_and_listener.job_batch.core import create_job_batch


def hakhana(req: HakhanaRequestModel, sched: BackgroundScheduler, cur) -> None:
    """
    Create a simple 'hakhana' group.
    - No media or custom messages.
    - invite_msg_title: "בבקשה להיכנס לקבוצה של ההכנה לקצונה שתתקיים ב {date}"
    - group_name: "הכנה לקצונה תקשוב {date}"
    - job_batch_name: "hakhana/{date}"
    """
    
    job_batch_name=f"hakhana/{req.date}"
    create_job_batch( job_batch_name, cur)
    
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
        job_batch_name=job_batch_name
    )

    group_id = create_group_and_invite(cur, hakhana_group)
    print(f"{group_name} group ID: {group_id}")
    return
