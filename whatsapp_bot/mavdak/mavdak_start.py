from zoneinfo import ZoneInfo
from datetime import datetime
from timezone import TIMEZONE
from apscheduler.schedulers.background import BackgroundScheduler
from models import MavdakRequestModel
from classes import WhatsappGroupCreate
from schedule_create_group import create_group_and_invite


# @dataclass
# class WhatsappGroupCreate:
#     messages: List[str]
#     name: str
#     participants: List[str]
#     invite_msg_title: str
#     media: List[str]
#     deadline: datetime
#     sched :  BackgroundScheduler
#     job_batch_name: str = ""  # which job_batch_name for jobs (e.g mavdaks/30.07 etc)

#     # Derived values
#     mavdak_date = req.base_date.strftime("%d/%m/%Y")
    

#     # Step 1 — Start the mavdak
#     mavdak_group_id = mavdak_start(
#         mavdak_date=mavdak_date,
#         forms_link=req.forms_link, #the forms link to set email - used to confirm attendance
#         iluzei_reaionot_mador_mavdak=req.iluzei_reaionot_mador_mavdak, # the iluzei reaionot send from mavdak group
#         group_participants=req.group_participants,
#         deadline=req.deadline_mavdak_list,
#         sched = sched, 
#     )

def mavdak_start(req : MavdakRequestModel, sched : BackgroundScheduler, job_batch_name : str, cur) -> str:
    
    """
    Create a WhatsApp group for the mavdak and send initial messages.

    Args:
        mavdak_date: Date string of the mavdak (e.g., "07/10/2025")
        forms_link: Link to the forms to be filled
        iluzei_reaionot_mador_mavdak: Additional instructions or info
        group_participants: List of phone numbers as strings (e.g., ["972532237008"])
        deadline: datetime object representing the deadline of the mavdak
    """
    
    # Derived values
    mavdak_date = req.base_date.strftime("%d/%m/%Y")

    group_messages = [f"""
    מועמדים יקרים,
    אנחנו מדור קצונה של אגף התקשוב. 
    המיון לקצונה ייערך באופן מקוון ויכלול מבחנים ממוחשבים וראיון זום עם פסיכולוג. 

    *המיון והראיונות לא מתקיימים באותו היום. המיון יהיה ב{mavdak_date} עבור כולם, ובהמשך נעדכן תאריכי ראיונות בקבוצה.*

    לקראת המבדק שמתקיים ב{mavdak_date}, הכנו כמה דגשים חשובים, יש לקרוא את כלל ההוראות באופן יסודי!

    ✅הכנות למבדק : 
    •יש לוודא כי יש לכם מחשב עם מצלמה לביצוע המבחנים 
    •אין אפשרות לבצע את המבחנים עם מחשב של אפל , התוכנה של המבחנים לא נפתחת במחשב הזה
    •אין אפשרות לבצע את המבחנים ללא מצלמה
    •המבדק הוא חובה , אין אפשרות להזיז תאריך ונדרש לעלות בזמן לביצוע המבחנים
    •במהלך השבוע שלאחר המבדק ישלחו אליכם פרטים על מועד ראיון הפסיכולוג - פרטי התחברות לזום (אין קישור- יש קוד), תאריך , שעה וסיסמה
    •את המבחנים ואת הראיון יש לערוך בחדר שקט ללא הפרעות חיצוניות. 

    • *אם מישהו לא מעוניין לצאת לקצונה/לדחות מחזור - להודיע בהקדם האפשרי!*

    ✅יום המבחנים :
    •ביום המבחנים , יישלח לכם מייל עם קישור למבחנים עצמם לקראת השעה 9:00
    •בשעה 9:00 יתקיים תדריך בזום לקראת המבחנים עצמם שאת הקישור אליו תקבלו כאן בקבוצה, לאחר סיום התדריך יש להיכנס לקישור של המבחן האישי ולהתחיל אותו
    •אם יש לכם תקלה בזמן המבחנים , תכתבו בקבוצה מה התקלה עם צילום של המסך מחשב 
    •בתמונת הקבוצה יש תקלות נפוצות , לפני שאתם כותבים בקבוצה על תקלה - תסתכלו אם יש את הפיתרון שלה בתמונה
    •אורך המבחנים הינו 4-5 שעות בממוצע ולכן יש לפנות את הזמן בהתאם לכך. 
    •יש לעלות למבחנים על מדים

    ✅יום ראיון הפסיכולוג :
    •אין לבצע את הראיון משטח פתוח , פוסלים על זה ראיון
    • יש לוודא שאתם נמצאים בחדר שקט ללא רעשים ושיש לכם קליטה
    •יש להכיר את מה שנכתב עליכם בחוו״ד 870 שכתב עליכם המפקד הישיר
    •במידה ועליתם לראיון והשיחה עוד לא התחילה , תכתבו בקבוצה כדי שנברר מול מדור מבדק
    •זמן הריאיון הוא בערך בין רבע שעה לעשרים דקות , משתנה בין חייל לחייל.
    •יש לעלות לראיון על מדים
    •ניתן להתחבר לראיון מאפליקציית זום בטלפון ויש להוריד את האפליקציה מראש למכשיר 
    •בתחילת הראיון תדרשו להציג חוגר ולענות על כמה שאלות אימות
    """,
        req.iluzei_reaionot_mador_mavdak,
        f"""
    היי לכולם. 
    בבקשה להזין את פרטיכם בקובץ הבא לקראת המבדק שיתקיים {mavdak_date} החל מהשעה 9:00.
    לוודא פעמיים שת.ז והמייל משוכתבים כמו שצריך

    {req.forms_link}
    """
        ]


    group_name = f"מבדק {mavdak_date}"
    group_invite_msg_title = f"בבקשה להצטרף לקבוצה של המבדק שיתקיים ב {mavdak_date}"
    
    
    mavdak_group = WhatsappGroupCreate(
        name=group_name,
        participants=req.group_participants,
        messages=group_messages,
        invite_msg_title=group_invite_msg_title,
        media=[],
        deadline=req.deadline_mavdak_list,  # fixed field name
        sched=sched,
        job_batch_name=job_batch_name    
    )

    mavdak_group_id = create_group_and_invite(cur, mavdak_group)
    
    # print(f"Mavdak group ID: {mavdak_group_id}")
    return mavdak_group_id


# -------------------------------
# Example usage:

# if __name__ == "__main__":
#     mavdak_start(
#         mavdak_date="07/10/2025",
#         forms_link="https://forms.example.com",
#         iluzei_reaionot_mador_mavdak="הנחיות נוספות מהמדריך",
#         group_participants=["972532237008", "972500000001"],
#         deadline=datetime(2025, 10, 7, 16, 0, tzinfo=ZoneInfo(TIMEZONE))
#     )
