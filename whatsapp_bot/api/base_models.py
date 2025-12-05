from pydantic import BaseModel, HttpUrl, Field
from typing import List
from datetime import date, datetime

# ---------------- Reusable type ----------------
# Each participant must be a valid Israeli phone number in +972 format
IsraeliPhoneNumber = 'constr(pattern=r"^972\\d{9}$")'

# ---------------- Models ----------------
class MavdakRequestModel(BaseModel):
    base_date: date
    deadline_mavdak_list: datetime
    forms_link: HttpUrl
    iluzei_reaionot_mador_mavdak: str

    # Each participant must be a valid Israeli phone number in +972 format
    group_participants: f'List[{IsraeliPhoneNumber}]' = Field(
        ...,  # required
        min_items=1
    )


# Request model
class Raf0RequestModel(BaseModel):
    date: date  # user provides the date in YYYY-MM-DD format
    
    group_participants: f'List[{IsraeliPhoneNumber}]' = Field(
        ...,  # required
        min_items=1
    )
    
class BaseGroupRequestModel(BaseModel):
    """
    Base model for group creation requests that require:
    - a date (YYYY-MM-DD)
    - a deadline (timezone-aware datetime)
    - a list of participants (Israeli phone numbers)
    """
    date: date
    deadline: datetime

    group_participants: f"List[{IsraeliPhoneNumber}]" = Field(
        ...,
        min_items=1,
    )
    
class HakhanaRequestModel(BaseGroupRequestModel):
    """
    Request model for הכנה (Hakhana)
    """
    pass


class VeadatKevaRequestModel(BaseGroupRequestModel):
    """
    Request model for ועדת קבע (Veadat Keva)
    """
    pass

    

class ChangeParticipantsRequestModel(BaseModel):
    gid: str  # any string for now
    participants: f'List[{IsraeliPhoneNumber}]' = Field(
        ...,        # required
        min_items=1  # at least one participant
    )
    

class GetParticipantsRequestModel(BaseModel):
    gid: str
    participants_to_exclude: f'List[{IsraeliPhoneNumber}]' = Field(
        ...,        # required
    )
    

class ParticipantItem(BaseModel):
    id: str
    phone_number: str


class SendMassMessagesRequestModel(BaseModel):
    message: str
    participants: List[ParticipantItem]
