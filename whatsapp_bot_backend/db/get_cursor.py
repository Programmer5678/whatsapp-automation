from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from .connection_str import connection_main

# Dependency for FastAPI
@contextmanager
def get_cursor(engine=None):

    
    engine = create_engine(connection_main) if not engine else engine
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    cur = SessionLocal()
    try:
        yield cur
    finally:
        cur.commit()
        cur.close()