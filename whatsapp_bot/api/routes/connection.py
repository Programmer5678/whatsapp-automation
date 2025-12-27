from fastapi import APIRouter
from api.base_models import ConnectRequestModel, ConnectionStateResponse
from whatsapp.core.whatsapp_connection import connect_service, connection_state_service

connection_router = APIRouter( prefix="/connection",)

@connection_router.get(
    "/connection_state",
    response_model=ConnectionStateResponse,
)
def connection_state_route():
    return {
        "status": connection_state_service()
    }


@connection_router.post("/connect")
def connect_route(payload: ConnectRequestModel):
    return connect_service(
        number=payload.number,
        api_key=payload.api_key,
    )