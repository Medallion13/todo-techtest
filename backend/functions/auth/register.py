import os
from typing import Any

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from shared.responses import error_response, success_response

logger = Logger(service="todo-api")
app = APIGatewayRestResolver()

cognito_client = boto3.client("cognito-idp")
user_pool_id = os.getenv("USER_POOL_ID", "")


@app.post("/auth/register")
def register_user() -> dict[str, Any]:
    """Register a new user in cognito"""
    try:
        body = app.current_event.json_body
        email = body.get("email")
        password = body.get("password")

        if not email or not password:
            return error_response("Email and password are requiered", 400)

        if "@" not in email:
            return error_response("Email not valid", 400)

        if len(password) < 8:
            return error_response("Password must be al least 8 characters", 400)

        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[{"Name": "email", "Value": email}, {"Name": "email_verified", "Value": "true"}],
            MessageAction="SUPPRESS",
            TemporaryPassword=password,
        )

        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id, Username=email, Password=password, Permanent=True
        )

        logger.info(f"User registerd: {email}")
        return success_response({"message": "User registered successfully", "email": email}, 201)

    except cognito_client.exceptions.UsernameExistsException:
        return error_response("User already exists", 409)

    except cognito_client.exceptions.InvalidPasswordException as e:
        return error_response(f"Invalid password: {str(e)}", 400)

    except Exception as e:
        logger.exception(f"Registration error, {e}")
        return error_response("Registration failed", 500)


@logger.inject_lambda_context
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler - entry point"""
    return app.resolve(event, context)
