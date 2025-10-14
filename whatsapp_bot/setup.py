from datetime import datetime
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

def setup_scheduler():

    jobstores = {
        'default': SQLAlchemyJobStore(url='postgresql+psycopg://codya:030103@localhost:5432/lsd?options=-csearch_path=public')
    }

    scheduler = BackgroundScheduler(jobstores=jobstores)
    scheduler.start()
    return scheduler
