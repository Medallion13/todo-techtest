import os
from typing import Any

import boto3
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from boto3.dynamodb.conditions import Key
from models.task import Task, TaskResponse
from shared.responses import error_response, success_response

logger = Logger(service="todo-api")
app = APIGatewayRestResolver()

dynamodb = boto3.resource("dynamodb")
table_name = os.getenv("TABLE_NAME", "")
table = dynamodb.Table(table_name)


@app.get("/tasks")
def list_tasks() -> dict[str, Any]:
    """List all tasks for authenticated user"""
    try:
        # Extraer user_id de Cognito claims
        auth_data = app.current_event.request_context.authorizer.claims
        user_id = auth_data.get("sub")

        if not user_id:
            return error_response("User ID not found in token", 401)

        # Query DynamoDB por PK (usuario)
        p_key = f"USER#{user_id}"

        logger.info(f"Listing tasks for user: {user_id}")

        response = table.query(KeyConditionExpression=Key("PK").eq(p_key) & Key("SK").begins_with("TASK#"))

        items = response.get("Items", [])

        # Convertir items de DynamoDB a TaskResponse
        tasks = []
        for item in items:
            try:
                task = Task.from_dynamodb_item(item)
                task_response = TaskResponse(
                    task_id=task.task_id,
                    title=task.title,
                    description=task.description,
                    status=task.status,
                    created_at=task.created_at.isoformat(),
                    updated_at=task.updated_at.isoformat(),
                )
                tasks.append(task_response.model_dump())
            except Exception as e:
                logger.warning(f"Error parsing task {item.get('SK')}: {str(e)}")
                continue

        logger.info(f"Found {len(tasks)} tasks")
        return success_response({"tasks": tasks, "count": len(tasks)}, 200)

    except AttributeError:
        # No hay authorizer (endpoint no protegido)
        return error_response("Unauthorized - No token provided", 401)

    except Exception as e:
        logger.exception("Error listing tasks")
        return error_response("Failed to list tasks", 500)


@logger.inject_lambda_context
def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda handler - entry point"""
    return app.resolve(event, context)
