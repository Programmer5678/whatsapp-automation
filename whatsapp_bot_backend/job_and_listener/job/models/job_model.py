from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any


@dataclass
class JobMetadata:
    id: str
    description: str
    batch_id: int


@dataclass
class JobAction:
    func: Any
    run_args: Dict[str, Any]


@dataclass
class JobSchedule:
    run_time: datetime
    coalesce: bool = True
    misfire_grace_time: int = 600


@dataclass
class Job:
    metadata: JobMetadata
    action: JobAction
    schedule: JobSchedule
