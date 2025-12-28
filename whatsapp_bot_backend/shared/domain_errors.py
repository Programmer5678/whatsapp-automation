

class DomainError(Exception):
    """
    Base class for all domain-level errors in your app.
    
    Optionally stores the request and response objects to help with debugging.
    """
    def __init__(self, message: str, request: any = None, response: any = None):
        self.message = message
        self.request = request
        self.response = response
        
        # Build full message including request/response if provided
        full_message = message
        if request is not None:
            full_message += f"\nRequest: {request}"
        if response is not None:
            full_message += f"\nResponse: {response}"
        
        super().__init__(full_message)


class EvolutionServerError(DomainError):
    """Raised when Evolution API server returns an error response."""
    def __init__(self, message: str = "Evolution API returned an error", request: any = None, response: any = None):
        super().__init__(message, request=request, response=response)

class ConnectionDomainError(EvolutionServerError):
    """Raised when there is a connection-level failure with Evolution API."""
    def __init__(self, message: str = "Connection error with Evolution API", request: any = None, response: any = None):
        super().__init__(message=message, request=request, response=response)


class JSONParseError(DomainError):
    """Raised when an external API returns a response that cannot be parsed as JSON."""
    def __init__(self, message: str = "Failed to parse API JSON response", request: any = None, response: any = None):
        super().__init__(message, request=request, response=response)


class WhatsappNotConnectedError(DomainError):
    """Raised when WhatsApp is not connected via Evolution API."""
    def __init__(self, message: str = "WhatsApp is not connected via Evolution API", request: any = None, response: any = None):
        super().__init__(message, request=request, response=response)



class CantRetrieveSchedulerJobError(DomainError):
    """Raised when unable to retrieve a job from the scheduler."""
    def __init__(self, message: str = "Cannot retrieve job from scheduler", request: any = None, response: any = None):
        super().__init__(message, request=request, response=response)