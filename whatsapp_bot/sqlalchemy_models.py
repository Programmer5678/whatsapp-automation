from sqlalchemy import Column, String, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from setup import Base

from sqlalchemy import Column, String, ForeignKey, Integer, Boolean
from sqlalchemy.orm import relationship

class GroupInfo(Base):
    __tablename__ = "group_info"

    group_id = Column(String(100), primary_key=True, index=True)

    # relationship to participants
    participants = relationship("Participants", back_populates="group")


class Participants(Base):
    __tablename__ = "participants"  # table name stays plural

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone_number = Column(String(100), nullable=False)
    group_id = Column(String(100), ForeignKey("group_info.group_id", ondelete="CASCADE"), nullable=False)

    # relationship back to group
    group = relationship("GroupInfo", back_populates="participants")
    

class MassMessages(Base):
    __tablename__ = "mass_messages"

    id =  Column(String(100), primary_key=True )
    phone_number = Column(String(100), nullable=False)
    success = Column(Boolean, nullable=True, default=False)   
    fail_reason = Column(String(255))
