from shared.domain_errors import ConnectionDomainError, WhatsappNotConnectedError
from whatsapp.core.evo_request import evo_request_with_retries   


def connection_state_service():
    try:
        resp = evo_request_with_retries(
            "instance/connectionState",
            method="GET"
        )
    except ConnectionDomainError:
        return "evolution_connection_error"

    content_type = resp.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            data = resp.json()
            if (
                isinstance(data, dict)
                and data.get("instance", {}).get("state") == "open"
            ):
                return "connected"
        except ValueError:
            pass

    return "not_connected"

def validate_whatsapp_connection():
    status = connection_state_service()
    if status != "connected":
        return WhatsappNotConnectedError(f"WhatsApp not connected. Current status: {status}")


def connect_service(
    number: str,
    api_key: str,
):
    resp_delete = evo_request_with_retries(
        "instance/delete",
        payload=None,
        params=None,
        method="DELETE",
    )

    resp_create = evo_request_with_retries(
        "instance/create",
        payload={
            "instanceName": "my_instance",
            "integration": "WHATSAPP-BAILEYS",
            "token": api_key,
            "number": number,
        },
        no_suffix=True,
    )

    resp_connect = evo_request_with_retries(
        "instance/connect",
        payload={"number": number},
        params=None,
        method="GET",
    )

    connect_json = resp_connect.json()

    return {
        "qr_code": connect_json.get("base64"),
        "delete_response": resp_delete.json(),
        "create_response": resp_create.json(),
        "connect_response": connect_json,
    }
