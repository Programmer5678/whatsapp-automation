import time
from typing import List, Callable
from warnings import warn

from evo_request import evo_request_with_retries
from evolution_framework import _phone_number

from typing import List, Callable, Optional
import time


class MassMessenger:
    def __init__(
        self,
        numbers: List[str],
        message: str,
        on_success: Optional[Callable[[str], None]] = None,
        on_failure: Optional[Callable[[str, str], None]] = None,  # now receives (phone, message)
    ):
        """
        Generalized messenger for sending messages to multiple participants.

        Args:
            numbers: List of participant phone numbers.
            message: Text message to send.
            on_success: Called after a successful send: on_success(phone).
            on_failure: Called on failure: on_failure(phone, message).
        """
        self.numbers = numbers
        self.message = message
        self.on_success = on_success
        self.on_failure = on_failure

    def send_all(self):
        for p in self.numbers:
            
            try:
            
                resp = evo_request_with_retries(
                    "message/sendText",
                    {
                        "number": _phone_number(p),
                        "text": self.message,
                        "delay": 50000,
                    },
                )
                
                if not resp.ok: 
                    raise Exception(f"HTTP {resp.status_code}: {resp.text}")
                
            except Exception as e:
                if self.on_failure:
                    self.on_failure(p, str(e))  
                    
                continue

            # success path → call on_success
            if self.on_success:
                self.on_success(p)

            time.sleep(10)
