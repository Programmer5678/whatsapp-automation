from datetime import datetime
from zoneinfo import ZoneInfo
from apscheduler.schedulers.background import BackgroundScheduler
from timezone import TIMEZONE
from send_stuff_to_group import send_messages_to_group
from classes import CreateJob

def send_mavdak_end_messages(mavdak_group_id: str):
    """
    Sends final mavdak messages to the specified WhatsApp group.
    """
    messages = [
        f"""
עליכם להיות זמינים לשיחת פתיחה החל מהשעה 9:00 — אך ייתכן והקישור יישלח עד השעה 10:00.
כשהקישור יתפרסם, נעלה אותו כאן. אין צורך לשלוח הודעות בנושא.

בין אם התחברתם לשיחה ובין אם לא — להלן הקישור למבדק.
https://keinan-sheffy.com/kst2/exam/login

זמן פתיחת המבחן המשוער הוא סביב השעה 10:00, אך יתכן ותוכלו להיכנס גם מוקדם יותר.
""",
        f"""
במקרים של תקלה טכנית יש לפנות ל:
035630594
+972 52-735-0191

מי שיש לו תקלה אחרת לשלוח בפורמט הבא:

בעיה במבחן המבד"ק  
שם מלא:  
מספר זהות:  
מייל:  
פלאפון:  
פירוט התקלה:  

כל הפניות מועברות למדור מבדק. מי שהפנייה שלו לא קיבלה מענה לאחר 45 דקות מוזמן לשלוח הודעה בווטסאפ למספר זה - אחרת נתעלם.
""",
        """
קראו שוב את ההנחיות ואת ההודעות מלעיל ושיהיה בהצלחה לכולם!
"""
    ]

    send_messages_to_group(messages, mavdak_group_id)
    print(f"Messages sent to group {mavdak_group_id}")




def mavdak_end(mavdak_group_id: str, when_to_send: datetime, sched: BackgroundScheduler, job_batch_name : str) -> None:
    """
    Schedule the sending of mavdak end messages at the given time,
    then shut down the scheduler immediately after.
    """

    # sched.add_job(
    #     send_mavdak_end_messages,   # the callable to run
    #     run_date=when_to_send,               
    #     args=[mavdak_group_id],     # positional arguments for that callable
    #     id=f"{job_batch_name}/mavdak_end"
    # )
    
    CreateJob(
        cur=None,  # Assuming cur is not needed for this job creation
        scheduler=sched,
        id=f"{job_batch_name}/mavdak_end",
        description="Send mavdak end messages",
        batch_id=job_batch_name,
        run_time=when_to_send,
        func=send_mavdak_end_messages,
        params={"mavdak_group_id": mavdak_group_id},
    )
    
    print(f"Scheduled messages for {when_to_send}")


# Example usage:
# if __name__ == "__main__":
#     mavdak_group_id = "120363422345335152@g.us"
#     when_to_send = datetime(2025, 10, 7, 9, 0, tzinfo=ZoneInfo("Asia/Jerusalem"))
#     mavdak_end(mavdak_group_id, when_to_send)
