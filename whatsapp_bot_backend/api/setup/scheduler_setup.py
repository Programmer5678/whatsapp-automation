
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from db.connection_str import connection_main
import logging
from typing import Optional, Callable, Any

from job_and_listener.listener import listener


def _setup_scheduler_logger(use_logging: bool = True, filename: str = "app.log") -> None:
    """
    Configure logging the same way your original code did.
    If use_logging is False we don't call basicConfig (so you can fall back to print).
    """
    if use_logging:
        logging.basicConfig(
            filename=filename,
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        logging.getLogger("apscheduler").setLevel(logging.DEBUG)
    # if use_logging is False: we intentionally do not configure logging so the code can use print

def _setup_scheduler_core(connection_url: str, listener_fn: Optional[Callable[[Any], None]] = None) -> BackgroundScheduler:
    """
    Build (but do not start) the BackgroundScheduler.
    Mirrors your original jobstores/listener setup.
    """
    jobstores = {
        "default": SQLAlchemyJobStore(url=connection_url)
    }

    scheduler = BackgroundScheduler(jobstores=jobstores)

    if listener_fn is not None:
        scheduler.add_listener(listener_fn)

    return scheduler

def setup_scheduler(use_logging: bool = True) -> BackgroundScheduler:
    """
    Public function that:
      1) sets up logging (if requested)
      2) builds scheduler core
      3) starts the scheduler
      4) returns the running scheduler
    Matches your original behaviour but with clearer internal separation.
    """
    # preserve your original log variable (debug or print)
    log = logging.debug if use_logging else print

    # 1) configure logging
    _setup_scheduler_logger(use_logging=use_logging)

    # 2) build scheduler (uses the module/global connection_main & listener like original)
    scheduler = _setup_scheduler_core(connection_main, listener)

    # 3) start scheduler (now that logging is configured)
    scheduler.start()
    log("Scheduler started")
    return scheduler


