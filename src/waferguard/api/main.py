"""FastAPI application. Demo decisions are isolated from authenticated reviewer cases."""

import os
import time
from functools import lru_cache
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from pydantic import BaseModel, Field, StrictInt

from waferguard.approval.authorization import Authorization, Forbidden
from waferguard.approval.store import Conflict, SQLiteStore
from waferguard.approval.workflow import ReviewService, public_case
from waferguard.inference.predict import ModelBundle

app = FastAPI(
    title="WaferGuard AI", version="0.4.0", docs_url="/api/docs", openapi_url="/api/openapi.json"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)


@lru_cache
def services():
    bundle = ModelBundle(os.getenv("WAFERGUARD_BUNDLE", "artifacts/release/bundle"))
    if os.getenv("WAFERGUARD_TABLE"):
        from waferguard.api.aws import cloud_services

        return cloud_services(bundle)
    auth = Authorization(secret=os.getenv("WAFERGUARD_SESSION_SECRET"))
    store = SQLiteStore(os.getenv("WAFERGUARD_DB", "artifacts/local/reviews.sqlite"))
    review = ReviewService(store, bundle.versions, auth.revalidate)
    return bundle, auth, review


def actor(authorization: str = Header(default="")):
    try:
        return services()[1].authenticate(authorization.removeprefix("Bearer "))
    except Forbidden as error:
        raise HTTPException(401, str(error)) from error


@app.exception_handler(Conflict)
async def conflict(request, error):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=409, content={"detail": str(error)})


@app.exception_handler(Forbidden)
async def forbidden(request, error):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=403, content={"detail": str(error)})


@app.exception_handler(KeyError)
async def missing(request, error):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=404, content={"detail": "Case or sample not found"})


@app.middleware("http")
async def headers(request, call_next):
    response = await call_next(request)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
            "X-Frame-Options": "DENY",
        }
    )
    return response


@app.get("/api/health")
def health():
    bundle, _, _ = services()
    return {
        "status": "ready",
        "region": "us-east-2",
        "versions": bundle.versions(),
        "simulated_disposition": True,
        "auto_accept": bundle.policy["enabled"],
    }


@app.get("/api/config")
def config():
    return {
        "region": "us-east-2",
        "cognito_domain": os.getenv("COGNITO_DOMAIN"),
        "client_id": os.getenv("COGNITO_CLIENT_ID"),
        "local_reviewer": os.getenv("WAFERGUARD_LOCAL_AUTH") == "1"
        and not os.getenv("AWS_LAMBDA_FUNCTION_NAME"),
    }


@app.post("/api/session/demo")
def demo_session():
    return {"token": services()[1].issue("demo"), "mode": "isolated simulation"}


@app.post("/api/session/local")
def local_session(request: Request):
    if not request.client or request.client.host not in {"127.0.0.1", "::1", "testclient"}:
        raise HTTPException(403, "Local reviewer mode requires loopback")
    return {"token": services()[1].issue("local"), "mode": "local development reviewer"}


@app.get("/api/catalog")
def catalog():
    return [
        {key: value for key, value in sample.items() if key != "wafer"}
        for sample in services()[0].samples
    ]


@app.get("/api/samples/{sample_id}")
def sample(sample_id: str):
    return next((sample for sample in services()[0].samples if sample["id"] == sample_id), None)


@app.get("/api/performance")
def performance():
    return services()[0].manifest["evaluation"]


class Inspection(BaseModel):
    sample_id: str | None = Field(default=None, max_length=128)
    wafer: list[list[StrictInt]] | None = Field(default=None, max_length=256)
    force_review: bool = False


@app.post("/api/inspect")
def inspect(
    payload: Inspection,
    identity: Annotated[dict, Depends(actor)],
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=128),
):
    bundle, _, review = services()
    if (payload.sample_id is None) == (payload.wafer is None):
        raise HTTPException(422, "Provide exactly one sample ID or wafer grid")
    wafer = payload.wafer
    sample_id = payload.sample_id
    if sample_id is not None:
        entry = next((s for s in bundle.samples if s["id"] == sample_id), None)
        if entry is None:
            raise HTTPException(404, "Sample not found")
        wafer = entry["wafer"]
    if wafer is None or not wafer or any(not row or len(row) > 256 for row in wafer):
        raise HTTPException(422, "Invalid wafer dimensions")
    start = time.perf_counter()
    try:
        prediction = bundle.predict(wafer)
    except (ValueError, TypeError) as error:
        raise HTTPException(422, str(error)) from error
    prediction["inference_ms"] = (time.perf_counter() - start) * 1000
    if sample_id is None:
        sample_id = "upload:" + prediction["input_hash"]
    result = review.create(
        identity, sample_id, prediction, bundle.policy, idempotency_key, payload.force_review
    )
    return public_case(result)


@app.get("/api/cases")
def cases(identity: Annotated[dict, Depends(actor)]):
    review = services()[2]
    return [
        public_case(review.get(identity, case["id"]))
        for case in review.store.list(identity["scope"])
    ]


@app.get("/api/cases/{case_id}")
def case(case_id: str, identity: Annotated[dict, Depends(actor)]):
    return public_case(services()[2].get(identity, case_id))


class Decision(BaseModel):
    expected_version: int = Field(ge=1)
    versions: dict[str, str]
    decision: Literal["approve", "correct", "reject"]
    label: str | None = Field(default=None, max_length=32)
    note: str = Field(min_length=3, max_length=512)


@app.post("/api/cases/{case_id}/decision")
def decide(
    case_id: str,
    payload: Decision,
    identity: Annotated[dict, Depends(actor)],
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=8, max_length=128),
):
    try:
        result = services()[2].decide(
            identity,
            case_id,
            payload.expected_version,
            payload.versions,
            payload.decision,
            payload.label,
            payload.note,
            idempotency_key,
        )
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    return public_case(result)


handler = Mangum(app, lifespan="off")
