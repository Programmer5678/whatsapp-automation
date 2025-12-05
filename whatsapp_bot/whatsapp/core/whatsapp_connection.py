from shared.domain_errors import WhatsappNotConnected
from whatsapp.core.evo_request import evo_request

def is_whatsapp_connected() -> bool:
    """
    Check if WhatsApp is connected via Evolution API.
    """
    
    # Replace 'whatsapp/status' with the actual endpoint method for checking WhatsApp
    response_json = evo_request(method="instance/connectionState", get=True).json()
        
    instance_info = response_json.get("instance", {})
    state = instance_info.get("state", "").lower()
        
    if state == "open":
        return True
    elif state == "close":
        return False
    else:
        raise Exception(f"Unexpected connection state: {state}")     
    
def validate_whatsapp_connection() -> None:
    
    """
    Validate that WhatsApp is connected. Raise an error if not.
    """
    
    if not is_whatsapp_connected():
        raise WhatsappNotConnected("WhatsApp is not connected via Evolution API.")
        
    
