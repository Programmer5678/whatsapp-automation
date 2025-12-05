from fastapi import Request
from db.get_cursor import get_cursor


def get_scheduler(request: Request):
    return request.app.state.scheduler


def get_cursor_dep(request : Request):
    engine = request.app.state.engine
    with get_cursor(engine=engine) as cur:
        yield cur  