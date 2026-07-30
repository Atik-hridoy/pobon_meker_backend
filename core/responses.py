from rest_framework.response import Response

class StandardResponse(Response):
    def __init__(self, success=True, message="", data=None, errors=None, status=None, **kwargs):
        payload = {
            "success": success,
            "message": message,
            "data": data,
            "errors": errors
        }
        super().__init__(data=payload, status=status, **kwargs)
