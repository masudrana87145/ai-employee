"""Small HTTP API for greetings and integer tasks."""

from __future__ import annotations

from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

SUPPORTED_TASKS: dict[str, str] = {
    "add": "Add two numbers",
    "mult": "Multiply two numbers",
    "sub": "Subtract the second number from the first",
}


class MessageResponse(BaseModel):
    """Successful response whose message is the result text."""

    message: str


class HealthResponse(BaseModel):
    """Liveness or readiness status."""

    status: str


class TaskRequest(BaseModel):
    """Integer task submitted in the request body."""

    model_config = ConfigDict(extra="forbid")

    task: str = Field(
        min_length=1,
        max_length=50,
        description="Task name: add, mult, or sub. Any letter case is accepted.",
        examples=["add"],
    )
    parm1: int = Field(strict=True, description="First integer.", examples=[5])
    parm2: int = Field(strict=True, description="Second integer.", examples=[4])


class TaskPurpose(BaseModel):
    """One supported task and what it does."""

    task: str
    purpose: str


class TaskErrorResponse(BaseModel):
    """Error body returned when the task name is not supported."""

    error: str
    valid_tasks: list[TaskPurpose]


class RootResponse(BaseModel):
    """Valid arithmetic operations and one sample task body."""

    operations: list[TaskPurpose]
    sample_payload: TaskRequest


SAMPLE_PAYLOAD = TaskRequest(task="add", parm1=5, parm2=4)


app = FastAPI(
    title="ai-employee API",
    version="0.1.0",
    description="Greeting query and add, multiply, or subtract tasks.",
)


def greet(name: str) -> str:
    """Return a greeting for *name*.

    Example:
        >>> greet("Masud")
        'Hi, Masud'
    """
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("name must not be empty")
    return f"Hi, {cleaned}"


def valid_tasks() -> list[TaskPurpose]:
    """Return the supported tasks in a stable order."""
    return [
        TaskPurpose(task=name, purpose=purpose) for name, purpose in SUPPORTED_TASKS.items()
    ]


def apply_task(task: str, parm1: int, parm2: int) -> str:
    """Apply a supported task and return the result sentence.

    *task* must already be normalized to lowercase.
    """
    if task == "add":
        return f"Sum of {parm1} and {parm2} is {parm1 + parm2}"
    if task == "mult":
        return f"Product of {parm1} and {parm2} is {parm1 * parm2}"
    if task == "sub":
        return f"Difference of {parm1} and {parm2} is {parm1 - parm2}"
    raise ValueError(task)


def task_error(task_name: str) -> JSONResponse:
    """Build the unsupported-task error, including every valid task."""
    shown = task_name.strip() or task_name
    body = TaskErrorResponse(
        error=f"Unsupported task '{shown}'.",
        valid_tasks=valid_tasks(),
    )
    return JSONResponse(status_code=400, content=body.model_dump())


@app.get("/", response_model=RootResponse, tags=["tasks"])
def root() -> RootResponse:
    """List the valid arithmetic operations and a sample JSON payload."""
    return RootResponse(operations=valid_tasks(), sample_payload=SAMPLE_PAYLOAD)


@app.get("/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    """Report that the process is running."""
    return HealthResponse(status="ok")


@app.get("/ready", response_model=HealthResponse, tags=["health"])
def ready() -> HealthResponse:
    """Report that the API can serve requests."""
    return HealthResponse(status="ready")


@app.get("/hi", response_model=MessageResponse, tags=["greeting"])
def say_hi(
    name: Annotated[
        str,
        Query(
            min_length=1,
            description="Text to greet, for example Masud.",
            examples=["Masud"],
        ),
    ],
) -> MessageResponse:
    """Greet the query-string value."""
    try:
        message = greet(name)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return MessageResponse(message=message)


@app.post(
    "/task",
    response_model=MessageResponse,
    responses={400: {"model": TaskErrorResponse}},
    tags=["tasks"],
)
def run_task(body: TaskRequest) -> MessageResponse | JSONResponse:
    """Add, multiply, or subtract parm1 and parm2."""
    normalized = body.task.strip().lower()
    if normalized not in SUPPORTED_TASKS:
        return task_error(body.task)
    return MessageResponse(message=apply_task(normalized, body.parm1, body.parm2))


def main() -> None:
    """Run the API on localhost port 8000."""
    import uvicorn

    uvicorn.run("api:app", host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
