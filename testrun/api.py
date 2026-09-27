from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

from testrun.store import store

app = FastAPI(title="Test Run API")


class CreateRunBody(BaseModel):
    name: str
    tests: list[str]


class ResultBody(BaseModel):
    test: str
    status: str
    duration_ms: int

    @field_validator("duration_ms", mode="before")
    @classmethod
    def reject_bool_duration(cls, value):
        # Runs before Pydantic coerces the raw JSON value into `int`.
        # By the time an `int` field sees the value, `true`/`false` has
        # already become `1`/`0`, so this has to happen here, not as an
        # isinstance check further down in the store.
        if isinstance(value, bool):
            raise ValueError("duration_ms must be an integer, not a boolean")
        return value


@app.exception_handler(RequestValidationError)
async def invalid_request(request, exc):
    return JSONResponse(status_code=400, content={"error": "invalid request"})


@app.exception_handler(ZeroDivisionError)
async def summary_failed(request, exc):
    return JSONResponse(status_code=500, content={"error": "internal error"})


@app.post("/api/runs", status_code=201)
def create_run(body: CreateRunBody):
    try:
        return store.create_run(body.name, body.tests)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.post("/api/runs/{run_id}/results")
def add_result(run_id: int, body: ResultBody):
    try:
        return store.add_result(run_id, body.test, body.status, body.duration_ms)
    except KeyError:
        return JSONResponse(status_code=404, content={"error": "run not found"})
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"error": str(exc)})


@app.get("/api/runs/{run_id}/summary")
def get_summary(run_id: int):
    try:
        return store.summary(run_id)
    except KeyError:
        return JSONResponse(status_code=404, content={"error": "run not found"})
