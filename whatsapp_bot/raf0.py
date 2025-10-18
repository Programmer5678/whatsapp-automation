from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
from evolution_framework import  WhatsappGroupCreate, create_group_and_invite
from models import Raf0RequestModel
from apscheduler.schedulers.background import BackgroundScheduler
from timezone import TIMEZONE

def calculate_deadline(req_date: date) -> datetime:
    """
    Given a date, returns a datetime representing the day before at 20:00 in the desired timezone.
    """
    day_before = req_date - timedelta(days=1)
    deadline_dt = datetime.combine(day_before, time(hour=20, minute=0, second=0))
    deadline_dt = deadline_dt.replace(tzinfo=ZoneInfo(TIMEZONE))
    return deadline_dt


# The actual function that does all the group creation
def raf0(req : Raf0RequestModel, sched: BackgroundScheduler) -> None:
    # Your original RAF0 "juice" code goes here
    group_name = f"רף 0 {req.date}"
    group_invite_msg_title = f"בבקשה להצטרף לקבוצה של הרף 0 שיתקיים ב {req.date}"

    group_messages = [
        """דגשים חשובים:
- הגעה עצאית לכניסה לקריית ההדרכה בשעה 13:30, לא תתאפשר כניסה לפניי ולא יתקבלו איחורים.
- שימו לב שהמיון הוא דו יומי ויש להביא ציוד לינה.
- נדרש להגיע עם חוגרים מקודדים
""",
        """
אנחנו יודעים שהדרך לבה״ד היא ארוכה… בואו נצעד אותה יחד! 💪🏻 בה״ד 1 ומדור הגפ״ה גאים להציג: אפליקציית מקראות ישראל הרישמית! שנועדה לפשט את הלמידה לקראת הקליטה לבה״ד 1. השימוש הינו חופשי ומומלץ להעברה ושיתוף עם כלל הצוערים שעתידים להיקלט לבה״ד. שיהיה המון בהצלחה! מדור גפ״ה בה״ד 1 🫶🏼 https://step-to-bhd1.web.app/home
""",
        """מצרפים את אפליקציית המקראות של בה"ד 1 לשימושכם"""
    ]

    media = "https://raw.githubusercontent.com/Programmer5678/uploads/main/raf0.jpeg"
    
    

    raf0_group = WhatsappGroupCreate(
        name=group_name,
        participants=req.group_participants,
        messages=group_messages,
        invite_msg_title=group_invite_msg_title,
        media=[media],
        sched=sched,
        deadline=calculate_deadline(req.date),
        dir=f"raf0/{req.date}"
    )
    
    
    
    raf0_group_id = create_group_and_invite(raf0_group)
    
    print(f"{group_name} group ID: {raf0_group_id }")
    
    return