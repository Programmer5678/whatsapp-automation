import json
from typing import List
from warnings import warn
from evolution_framework import _phone_number, get_group_invite_link, get_group_member_ids
from evo_request import evo_request_with_retries
import time
from sqlalchemy import text



class JobbingAround:
    
    def __init__(self, job_name: str, cur):
        self.cur = cur
        self.job_name = job_name

    def run(self, invite_msg_title: str, media, messages, group_id: str):
        # call the core using instance state
        self.job_function_core(invite_msg_title, media, messages, group_id)

    def job_function_core(self, invite_msg_title: str, media, messages, group_id: str):
        participants = list(
            self.cur.execute(
                text("select phone_number from participants where group_id = :gid"),
                {"gid": group_id},
            ).fetchall()
        )

        # keep original logic: call the instance helper and other funcs
        self.handle_failed_adds(invite_msg_title, group_id)
        self.send_stuff(media, messages, group_id)

    def handle_failed_adds(self, invite_msg_title: str, group_id: str) -> None:
        # use helpers that now are instance methods
        actual_members = set(get_group_member_ids(group_id))
        participants = list(
            self.cur.execute(
                text("select phone_number from participants where group_id = :gid"),
                {"gid": group_id},
            ).fetchall()
        )
        failed_to_add = self.compute_failed_to_add(participants, actual_members)

        if failed_to_add:
            invite_link = get_group_invite_link(group_id)
            self.send_invite_to_failed(failed_to_add, invite_link, invite_msg_title)

    def send_stuff(self, media, messages, group_id):
        pass

    def compute_failed_to_add(self, participants: List[str], actual_members: set) -> List[str]:
        """Return list of normalized participants that were not added to the group."""
        return [_phone_number(p) for p in participants if _phone_number(p) not in actual_members]

    def add_issue_to_job_sql(self, issue):
        """
        Add an issue to a job in the job_information table.

        Args:
            issue: Python object representing the issue (will be JSON-serialized)
        """
        self.cur.execute(
            text(
                """
                UPDATE job_information
                SET issues =  array_append( issues, :issue_json )
                WHERE id = :job_name
                """
            ),
            {
                "issue_json": json.dumps(issue),
                "job_name": self.job_name,
            },
        )

    def send_invite_to_failed(self, failed_to_add: List[str], invite_link: str, invite_msg_title: str) -> None:
        message = f"{invite_msg_title}\n\n{invite_link}"
        for p in failed_to_add:
            resp = evo_request_with_retries(
                "message/sendText",
                {
                    "number": _phone_number(p),
                    "text": message,
                    "delay": 50000,
                },
            )

            try:  # if resp is error because participant doesnt exist --> just warn and handle
                assert resp.json()["response"]["message"][0]["exists"] is False

                # use instance method to record the issue
                self.add_issue_to_job_sql(
                    {
                        "participant": p,
                        "issue": "does not exist - could not send invite. skipping. ",
                    }
                )

                warn(f"Error in job {self.job_name}: Participant {p} does not exist — skipping.")
            except Exception:
                resp.raise_for_status()

            time.sleep(10)

    # if you also want a version that handles failed adds using explicit participants list:
    def handle_failed_adds_with_participants(self, participants: List[str], invite_msg_title: str, group_id: str):
        """
        Alternate entry if you already have participants list and want to reuse the logic.
        (This preserves original capability without changing core logic.)
        """
        actual_members = set(get_group_member_ids(group_id))
        failed_to_add = self.compute_failed_to_add(participants, actual_members)

        if failed_to_add:
            invite_link = get_group_invite_link(group_id)
            self.send_invite_to_failed(failed_to_add, invite_link, invite_msg_title)
    
