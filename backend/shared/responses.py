import json
from typing import Any


def success_response(data: dict[str, Any], status_code: int = 200) -> dict[str, Any]:
    """
    Genera respuesta exitosa estandarizada para API Gateway.

    Args:
        data: Datos a devolver en el body
        status_code: Código HTTP (200, 201, etc.)

    Returns:
        Dict con formato esperado por API Gateway
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "http://localhost:5173",  # CORS
            "Access-Control-Allow-Credentials": "true",
        },
        "body": json.dumps(data, ensure_ascii=False),  # ensure_ascii para UTF-8
    }


def error_response(message: str, status_code: int = 500) -> dict[str, Any]:
    """
    Genera respuesta de error estandarizada.

    Args:
        message: Mensaje de error descriptivo
        status_code: Código HTTP de error (400, 404, 500, etc.)

    Returns:
        Dict con formato esperado por API Gateway
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "http://localhost:5173",
        },
        "body": json.dumps({"error": message}, ensure_ascii=False),
    }
