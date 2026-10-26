from fastapi import APIRouter, Query, Body, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from app.services.ai_analyst_service import ai_analyst_service

router = APIRouter(prefix="/api/ai", tags=["Stock AI Copilot & Analyst"])

class AnalyzeStockRequest(BaseModel):
    symbol: str
    custom_prompt: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    symbol: Optional[str] = "NIFTY"
    provider: Optional[str] = None
    api_key: Optional[str] = None

class UpdateConfigRequest(BaseModel):
    provider: Optional[str] = None
    gemini_key: Optional[str] = None
    openai_key: Optional[str] = None
    groq_key: Optional[str] = None

@router.get("/config")
def get_ai_config():
    """
    Returns configured AI providers, status, and supported models.
    """
    return ai_analyst_service.get_config()

@router.post("/config")
def update_ai_config(payload: UpdateConfigRequest):
    """
    Updates the active AI provider or registers API keys in memory.
    """
    return ai_analyst_service.update_config(
        provider=payload.provider,
        gemini_key=payload.gemini_key,
        openai_key=payload.openai_key,
        groq_key=payload.groq_key
    )

@router.post("/analyze-stock")
async def analyze_stock(payload: AnalyzeStockRequest):
    """
    Performs deep AI market analysis for any stock symbol (NSE / BSE) using
    live quotes, pivots, indicators, open interest confluence, and multi-horizon forecasts.
    """
    try:
        return await ai_analyst_service.analyze_stock(
            symbol=payload.symbol,
            custom_prompt=payload.custom_prompt,
            provider=payload.provider,
            api_key=payload.api_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat")
async def chat_with_copilot(payload: ChatRequest):
    """
    Conversational AI Chat seeded with the currently viewed stock's real-time indicators and levels.
    """
    try:
        messages_dicts = [{"role": m.role, "content": m.content} for m in payload.messages]
        return await ai_analyst_service.chat(
            messages=messages_dicts,
            symbol=payload.symbol,
            provider=payload.provider,
            api_key=payload.api_key
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
