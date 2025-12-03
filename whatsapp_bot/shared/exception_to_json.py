import json
import traceback


def exception_to_json(e: Exception) -> None:
    
    exc_dict = {
        "type": type(e).__name__,
        "message": str(e),
        "stack_trace": traceback.format_exc()
    }
    json_string = json.dumps(exc_dict)
    
    return json_string