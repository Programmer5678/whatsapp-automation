


import logging
from typing import List
from base_job_classes.base_job import BaseJob
from send_stuff_to_group import send_messages_to_group


class MavdakEndJob(BaseJob):
    """
    Add participants to an existing WhatsApp group in batches of 20.
    """

    def run(self, mavdak_group_id: str) -> None:
        # Add participants in batches
        self.send_mavdak_end_messages(mavdak_group_id=mavdak_group_id)

    def send_mavdak_end_messages(self, mavdak_group_id: str, use_logging: bool = True) -> None:
        """
        Sends final mavdak messages to the specified WhatsApp group.
        """
        
        log = logging.debug if use_logging else print
        
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
        log(f"Messages sent to group {mavdak_group_id}")
