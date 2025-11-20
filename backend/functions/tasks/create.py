import os
import uuid
from datetime import UTC, datetime
from typing import Any

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from models.task import CreateTaskDto, Task, TaskResponse
from shared.responses import error_response, success_response

logger = Logger(service="todo-api")
app = APIGatewayRestResolver()


# inicializacion de servicios
dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("TABLE_NAME", "")
table = dynamodb.Table(table_name)


@app.post("/tasks")
def create_task() -> dict[str, Any]:
    try:
        response = app.current_event.json_body
        task_dto = CreateTaskDto(**response)

        # Crear ID
        now = datetime.now(UTC)

        # exrtact user_id from cognito
        try:
            auth_data = app.current_event.request_context.authorizer.claims
            user_id = auth_data.get("sub")

            if not user_id:
                logger.error("User ID not found in token claims")
                return error_response("Unauthorized - Invalid token", 401)

        except AttributeError:
            logger.warning("No authorizer found - using test user")
            user_id = "test_user"

        generated_task_id = str(uuid.uuid4())

        new_task = Task(
            task_id=generated_task_id,
            user_id=user_id,
            title=task_dto.title,
            description=task_dto.description,
            status=task_dto.status,
            created_at=now,
            updated_at=now,
        )

        # save to dynamo
        dynamo_task = new_task.to_dynamodb_item()

        logger.info(f"Guardando task {generated_task_id}")
        table.put_item(Item=dynamo_task)

        # Struct the response
        response_model = TaskResponse(
            task_id=new_task.task_id,
            title=new_task.title,
            description=new_task.description,
            status=new_task.status,
            created_at=new_task.created_at.isoformat(),
            updated_at=new_task.updated_at.isoformat(),
        )

        # Retornamos la respuesta
        return success_response(response_model.model_dump(), status_code=201)

    except ValueError as e:
        # pandytic validation errors
        logger.error(f"Error de validación: {str(e)}")
        return error_response(f"Datos inválidos: {str(e)}", status_code=400)

    except Exception as e:
        # errores generales TODO: darle mas granularidad
        logger.exception(f"Error interno crítico, {e}")
        return error_response("Error interno del servidor", status_code=500)


@logger.inject_lambda_context
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler - entry point"""
    return app.resolve(event, context)
