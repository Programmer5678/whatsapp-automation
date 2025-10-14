from pydantic import BaseModel, constr, HttpUrl, Field
from typing import List
from datetime import date, datetime

class MavdakRequestModel(BaseModel):
    base_date: date
    deadline_mavdak_list: datetime
    forms_link: HttpUrl
    iluzei_reaionot_mador_mavdak: str

    # Each participant must be a valid Israeli phone number in +972 format
    group_participants: List[constr(pattern=r'^972\d{9}$')] = Field(
        ...,  # required
        min_items=1
    )

