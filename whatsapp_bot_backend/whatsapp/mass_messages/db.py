from typing import Dict, List, Any
from sqlalchemy import text

from api.base_models import ParticipantItem
from job_and_listener.job.models.job_model import Job


def insert_to_mass_messages_sql(
    cur, batch_id: str, mass_messages_tb_participants : List[Dict[str, Any]]
):

    insert_sql = text("""
        INSERT INTO mass_messages (
            batch_id, recipient_id, recipient_phone_number, job_info_id
        ) VALUES (
            :batch_id, :recipient_id, :recipient_phone_number, :job_info_id
        )
    """)

    for el in mass_messages_tb_participants:
        
        participantItem = el["participantItem"]
        job_id = el["job_id"]
        
        cur.execute(
            insert_sql,
            {
                "batch_id": batch_id,
                "recipient_id": participantItem.id,
                "recipient_phone_number": participantItem.phone_number,
                "job_info_id": job_id,
            }
        )

