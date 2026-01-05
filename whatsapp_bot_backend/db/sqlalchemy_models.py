# SQLAlchemy core imports
from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, ARRAY, ForeignKey, DateTime, func, PrimaryKeyConstraint
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

# Project-specific import
from job_and_listener.job_status import JOBSTATUS


Base = declarative_base()

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

    # Foreign key to JobBatch
    batch_id = Column(
        String(100),
        ForeignKey("job_batch.name", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    recipient_id = Column(String(100), nullable=False)
    recipient_phone_number = Column(
        String(100),
        nullable=False,
    )
    

    # Foreign key to JobInformation.id
    job_info_id = Column(
        String(200),
        ForeignKey("job_information.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    success = Column(Boolean, nullable=True, default=False)
    fail_reason = Column(JSON, nullable=True)
    
    __table_args__ = (
        PrimaryKeyConstraint("batch_id", "recipient_id"),
    )


class JobBatch(Base):
    __tablename__ = "job_batch"

    name = Column(String(100), primary_key=True)
    description = Column(String(255), nullable=True)
 


# Postgres ENUM type (create_type=True will instruct SQLAlchemy to emit CREATE TYPE when using
# metadata.create_all; prefer migrations for production)
jobstatus_enum = PG_ENUM(
    *JOBSTATUS.values(),
    name="jobstatus",
    create_type=True,
)


class JobInformation(Base):
    __tablename__ = "job_information"


    id = Column(String(200), primary_key=True)
    description = Column(Text, nullable=False)


    # status uses the Postgres ENUM, defaults to PENDING
    status = Column(jobstatus_enum, nullable=False, server_default=JOBSTATUS["PENDING"] )


    # foreign key to apscheduler_jobs.id; nullable because the job row may be deleted
    job_id = Column(String, ForeignKey("apscheduler_jobs.id", ondelete="SET NULL", use_alter=True,), nullable=True, index=True)
    
    # Foreign key to job_batch with ON DELETE CASCADE
    batch_id = Column(String, ForeignKey("job_batch.name", ondelete="CASCADE"), nullable=False, index=True)
    
    
    issues = Column(ARRAY(JSON), nullable=True)
    
    exception = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

