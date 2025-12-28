import json
import traceback


def exception_to_json(e: Exception) -> None:
    
    # Get the traceback object from the exception itself
    tb = e.__traceback__
    
    exc_dict = {
        "type": type(e).__name__,
        "message": str(e),
        "stack_trace": "".join(traceback.format_tb(tb))
    }
    json_string = json.dumps(exc_dict)
    
    return json_string