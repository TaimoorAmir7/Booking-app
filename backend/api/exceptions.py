from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        payload = {"error": response.data}
        if isinstance(response.data, dict) and "detail" in response.data:
            payload = {"error": str(response.data["detail"])}
        response.data = payload
        return response

    return Response(
        {"error": "Internal server error"},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
