from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse

def custom_exception_handler(exc, context):
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    # Now add the HTTP status code to the response.
    if response is not None:
        errors = response.data
        message = "An error occurred."
        
        # If it's a validation error, extract the message
        if isinstance(exc, ValidationError):
            message = "Validation failed."
            
        # Print the exact error to the terminal for easier debugging
        print(f"\n[API ERROR - 400 Bad Request] Endpoint: {context['request'].path}")
        print(f"Exact Validation Errors: {errors}\n")
            
        custom_response = {
            "success": False,
            "message": message,
            "data": None,
            "errors": errors
        }
        response.data = custom_response

    return response
