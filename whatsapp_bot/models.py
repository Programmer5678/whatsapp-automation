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


# Request model
class Raf0RequestModel(BaseModel):
    date: date  # user provides the date in YYYY-MM-DD format
    
    group_participants: List[constr(pattern=r'^972\d{9}$')] = Field(
        ...,  # required
        min_items=1
    )
    
# Request model for חֲכָנָה
class HakhanaRequestModel(BaseModel):
    date: date  # YYYY-MM-DD
    # deadline is provided directly by the caller (already a timezone-aware datetime if needed)
    deadline: datetime

    group_participants: List[constr(pattern=r'^972\d{9}$')] = Field(
        ...,  # required
        min_items=1
    )
    
    

class ChangeParticipantsRequestModel(BaseModel):
    gid: str  # any string for now
    participants: List[constr(pattern=r'^972\d{9}$')] = Field(
        ...,        # required
        min_items=1  # at least one participant
    )
    
class GetParticipantsRequestModel(BaseModel):
    gid : str
    participants_to_exclude: List[constr(pattern=r'^972\d{9}$')] = Field(
        ...,        # required
    )