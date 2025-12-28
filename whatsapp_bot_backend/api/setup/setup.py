"""
Scheduler and database setup module for the application.

This module initializes the APScheduler instance used for handling
scheduled tasks (e.g., WhatsApp mass-messaging jobs) and configures
logging for scheduler-related events. It also creates required SQLAlchemy
tables on application startup.

The `setup(app)` function is intended to be called from the FastAPI
startup event. It:

  • configures and starts the BackgroundScheduler  
  • attaches the scheduler and database engine to `app.state`  
  • ensures all required SQLAlchemy tables exist

Split into small helper functions for clarity:
  - `_setup_scheduler_logger` manages logging configuration  
  - `_setup_scheduler_core` constructs the scheduler  
  - `setup_scheduler` wires everything together and starts it  
  - `create_tables` creates SQL tables referenced by scheduled jobs
"""



from db.connection_str import connection_main
from sqlalchemy import create_engine
from db.create_tables import create_tables
from .scheduler_setup import setup_scheduler

def setup(app):
    app.state.scheduler = setup_scheduler()
    app.state.engine = create_engine(connection_main)
    create_tables( engine=app.state.engine  )





        

        
      
        
        












