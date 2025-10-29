import time
from typing import List, Callable
from warnings import warn

from evo_request import evo_request_with_retries
from evolution_framework import _phone_number

class MassMessenger:
    def __init__(
        self,
        numbers: List[str],
        message: str,
        on_success: Callable[[str], None] = None,
        on_failure: Callable[[str], None] = None,
    ):
        """
        Generalized messenger for sending messages to multiple participants.

        Args:
            numbers: List of participant phone numbers.
            message: Text message to send.
            on_success: Called after a successful send.
            on_failure: Called only if participant doesn't exist.
        """
        self.numbers = numbers
        self.message = message
        self.on_success = on_success
        self.on_failure = on_failure

    def send_all(self):
        for p in self.numbers:
            resp = evo_request_with_retries(
                "message/sendText",
                {
                    "number": _phone_number(p),
                    "text": self.message,
                    "delay": 50000,
                },
            )

            try:
                # participant doesn't exist → warn & call on_failure
                assert resp.json()["response"]["message"][0]["exists"] is False
                warn(f"Participant {p} does not exist — skipping.")
                if self.on_failure:
                    self.on_failure(p)
                    
                

            except Exception:
                resp.raise_for_status()
            
            # success path → call on_success
            if self.on_success:
                self.on_success(p)

            time.sleep(10)
