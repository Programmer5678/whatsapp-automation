from typing import Dict
from sqlalchemy import text

from api.base_models import ParticipantItem
from job_and_listener.job.models.job_model import Job


def insert_to_mass_messages_sql(
    cur, batch_id: str, job_dict: Dict[ParticipantItem, "Job"]
):
    """
    Inserts participants into mass_messages table with the corresponding job_info_id.
    Assumes participants and job_list are in the same order.

    Args:
        cur: DB cursor
        participants: list of participant objects with 'id' and 'phone_number'
        batch_id: the batch ID for this insert
        job_list: list of Job objects corresponding to participants
    """
    insert_sql = text("""
        INSERT INTO mass_messages (
            batch_id, recipient_id, recipient_phone_number, job_info_id
        ) VALUES (
            :batch_id, :recipient_id, :recipient_phone_number, :job_info_id
        )
    """)

    for participant, job in job_dict.items():
        cur.execute(
            insert_sql,
            {
                "batch_id": batch_id,
                "recipient_id": participant.id,
                "recipient_phone_number": participant.phone_number,
                "job_info_id": job.metadata.id,
            }
        )

