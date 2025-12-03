def create_tables(engine):
    
    from whatsapp_bot.db.sqlalchemy_models import GroupInfo, Participants, MassMessages, JobBatch, JobInformation  # import your models

    # Only create these two tables
    GroupInfo.__table__.create(bind=engine, checkfirst=True)
    Participants.__table__.create(bind=engine, checkfirst=True)
    MassMessages.__table__.create(bind=engine, checkfirst=True)
    JobBatch.__table__.create(bind=engine, checkfirst=True)
    JobInformation.__table__.create(bind=engine, checkfirst=True)
    