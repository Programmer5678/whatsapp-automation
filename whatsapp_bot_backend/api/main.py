from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.group_creates import group_creates_router
from routes.job import job_router
from routes.test_routes import test_router
from routes.group_participants import participants_router
from routes.send_mass_messages import messages_router
from routes.connection import connection_router


from api.setup.setup import setup


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,  # MUST be False when using "*"
    allow_methods=["*"],
    allow_headers=["*"],
)
# Register routers
for router in [group_creates_router, job_router, test_router, participants_router, messages_router, connection_router ]:
    app.include_router(router)


@app.on_event("startup")
def startup_event():
    setup(app)



@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down scheduler...")
    app.state.scheduler.shutdown()
    print("Scheduler shut down.")