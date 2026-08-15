from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import Settings, get_settings
from app.schemas.api import GenerateRequest, GenerateResponse, HealthResponse
from app.services.agent import StructuredOutputAgent

router = APIRouter()


def get_agent(request: Request) -> StructuredOutputAgent:
    return request.app.state.agent


@router.get("/health", response_model=HealthResponse, tags=["system"])
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    return HealthResponse(service=settings.app_name)


@router.post("/v1/generate", response_model=GenerateResponse, tags=["generation"])
async def generate(
    payload: GenerateRequest,
    settings: Settings = Depends(get_settings),
    agent: StructuredOutputAgent = Depends(get_agent),
) -> GenerateResponse:
    retries = payload.max_retries if payload.max_retries is not None else settings.max_retries
    try:
        return await agent.run(
            prompt=payload.prompt,
            schema_name=payload.schema_name,
            max_retries=retries,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
