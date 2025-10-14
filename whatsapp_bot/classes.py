from dataclasses import dataclass, field
from typing import List, Callable
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
    dir: str = ""  # which dir for jobs (e.g mavdaks/30.07 etc)



@dataclass
class JobInfo:
    scheduler: BackgroundScheduler
    function: Callable
    params: dict = field(default_factory=dict)  # default to empty dict if not provided
    dir : str = ""  # which dir for jobs (e.g mavdaks/30.07 etc)