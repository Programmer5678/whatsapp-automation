from dataclasses import dataclass, field
import logging
from typing import List, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from datetime import datetime
from typing import Any, Optional, Dict
from sqlalchemy import text

from job_status import JOBSTATUS



# --- Simple container you asked for ---
@dataclass
class WhatsappGroupCreate:
    messages: List[str]
    name: str
    participants: List[str]
    invite_msg_title: str
    media: List[str]
    deadline: datetime
    sched :  BackgroundScheduler
    job_batch_name: str = ""  # which dir for jobs (e.g mavdaks/30.07 etc)
    

