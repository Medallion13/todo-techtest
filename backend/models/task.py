from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """ """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class CreateTaskDto(BaseModel):
    """DTO"""

    title: str = Field(..., min_length=1, max_length=200, description="Título de la tarea")
    description: str | None = Field(None, max_length=1000, description="Descripción opcional")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Estado inicial")


class Task(BaseModel):
    """ """

    task_id: str = Field(..., description="UUID único de la tarea")
    user_id: str = Field(..., description="ID del usuario propietario")
    title: str
    description: str | None = None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    def to_dynamodb_item(self) -> dict:
        """Convierte Task a formato DynamoDB item"""
        return {
            "PK": f"USER#{self.user_id}",
            "SK": f"TASK#{self.task_id}",
            "task_id": self.task_id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dynamodb_item(cls, item: dict) -> "Task":
        """Crea Task desde item de DynamoDB"""
        return cls(
            task_id=item["task_id"],
            user_id=item["PK"].replace("USER#", ""),
            title=item["title"],
            description=item.get("description"),
            status=TaskStatus(item["status"]),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
        )


class TaskResponse(BaseModel):
    """DTO"""

    task_id: str
    title: str
    description: str | None = None
    status: TaskStatus
    created_at: str  # ISO format string
    updated_at: str
