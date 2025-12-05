from fastapi import FastAPI


from routes.group_creates import group_creates_router
from routes.job import job_router
from routes.test_routes import test_router
from routes.group_participants import participants_router
from routes.send_mass_messages import messages_router


from api.setup.setup import setup


app = FastAPI()

# Register routers
for router in [group_creates_router, job_router, test_router, participants_router, messages_router ]:
    app.include_router(router)


@app.on_event("startup")
def startup_event():
    setup(app)



@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down scheduler...")
    app.state.scheduler.shutdown()
    print("Scheduler shut down.")