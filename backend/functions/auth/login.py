import os
from typing import Any

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from shared.responses import error_response, success_response

logger = Logger(service="todo-api")
app = APIGatewayRestResolver()

cognito_client = boto3.client("cognito-idp")
client_id = os.getenv("USER_POOL_CLIENT_ID", "")


@app.post("/auth/login")
def login_user() -> dict[str, Any]:
    """login flow with cognito"""

    try:
        body = app.current_event.json_body
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            return error_response("Email and password are required", 400)

        # cognito auth
        response = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
            },
        )

        # Tokens
        auth_result = response["AuthenticationResult"]
        id_token = auth_result.get("IdToken")
        access_token = auth_result.get("AccessToken")
        refresh_token = auth_result.get("RefreshToken")
        expires_in = auth_result.get("ExpiresIn")

        logger.info(f"User logged in: {email}")
        return success_response(
            {
                "message": "Login successful",
                "idToken": id_token,
                "accessToken": access_token,
                "refreshToken": refresh_token,
                "expiresIn": expires_in,
            },
            200,
        )

    except cognito_client.exceptions.NotAuthorizedException:
        return error_response("Invalid email or password", 401)

    except cognito_client.exceptions.UserNotFoundException:
        return error_response("User not found", 404)

    except cognito_client.exceptions.UserNotConfirmedException:
        return error_response("User not confirmed", 403)

    except Exception as e:
        logger.exception("Login error, {e}")
        return error_response("Login failed", 500)


@logger.inject_lambda_context
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler - entry point"""
    return app.resolve(event, context)
