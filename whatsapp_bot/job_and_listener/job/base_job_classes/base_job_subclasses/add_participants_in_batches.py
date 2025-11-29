import logging
import time
from typing import List
from warnings import warn
from evo_request import evo_request_with_retries
from evolution_framework import _phone_number
from job_and_listener.job.base_job_classes.base_job import BaseJob



class AddParticipantsInBatchesJob(BaseJob):

    """
    Add participants to an existing WhatsApp group in batches of 20.
    """

    def run(self, *, group_id: str, participants: List[str]) -> None:
        self.add_participants_in_batches(group_id, participants)
        


    def add_participants_in_batches(self, group_id: str, participants: List[str], use_logging=False) -> None:
        """
        Add participants to an existing WhatsApp group in batches of 20.
        """
            
        log = logging.debug if use_logging else print

        log(f"[START] Adding participants to group {group_id}")
        log(f"[INFO] Total participants: {len(participants)}")

        def get_batches(items, batch_size=20):
            for i in range(0, len(items), batch_size):
                yield items[i : i + batch_size]

        for batch in get_batches(participants):
            log(f"[BATCH] Next batch ({len(batch)} participants): {batch}")

            payload = {
                "action": "add",
                "participants": [_phone_number(p) for p in batch]
            }

            log(f"[REQUEST] Sending payload: {payload}")

            resp = evo_request_with_retries(
                "group/updateParticipant",
                payload,
                params={"groupJid": group_id}
            )

            log(f"[RESPONSE] status={resp.status_code}, text={resp.text[:200]}")

            if resp.status_code == 400:
                warn_msg = f"⚠️ Warning: Bad request for group {group_id} — {resp.text}. Maybe becuase some participants cant be added?"
                self.add_issue_to_job_sql({"issue": warn_msg})
                log(warn_msg)
            else:
                resp.raise_for_status()
                log(f"[SUCCESS] Batch added successfully")

            log("[SLEEP] Waiting 10 seconds before next batch...")
            time.sleep(10)

        log(f"[END] Finished adding participants to group {group_id}")

