from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from setup import Base

class GroupInfo(Base):
    __tablename__ = "group_info"

    group_id = Column(String(100), primary_key=True, index=True)
    participants = Column(ARRAY(String(100)), nullable=False, default=[])
