from contextlib import contextmanager
from datetime import datetime
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base



connection_prefix = 'postgresql+psycopg://codya:030103@localhost:5432/'
connection_apischeduler = connection_prefix + 'lsd'
connection_main = connection_prefix + 'main'


def setup_scheduler():

    jobstores = {
        'default': SQLAlchemyJobStore(url=connection_apischeduler)
    }

    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.start()
    return scheduler







engine = create_engine(connection_main)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Dependency for FastAPI
@contextmanager
def get_cursor():
    cur = SessionLocal()
    try:
        yield cur
    finally:
        cur.commit()
        cur.close()
        
def get_cursor_dep():
    with get_cursor() as cur:
        yield cur
        
def create_tables():
    from sqlalchemy_models import GroupInfo, Participants, MassMessages  # import your models

    # Only create these two tables
    GroupInfo.__table__.create(bind=engine, checkfirst=True)
    Participants.__table__.create(bind=engine, checkfirst=True)
    MassMessages.__table__.create(bind=engine, checkfirst=True)




import logging

logging.basicConfig(
    filename='app.log',        # path to your log file
    level=logging.DEBUG,       # minimum level to record
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)