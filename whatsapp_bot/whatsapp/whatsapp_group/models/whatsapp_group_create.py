from dataclasses import dataclass
from typing import List
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime




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
    

