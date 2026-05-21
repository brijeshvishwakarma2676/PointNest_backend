from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import logging

from app.config.database import get_db
from app.core.dependencies import get_current_user
from app.services.ai.ai_agent import process_merchant_query
from app.utils import response_parser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

class ChatMessage(BaseModel):
    sender: str
    text: str

class ChatRequest(BaseModel):
    query: str
    history: list[ChatMessage] = []

@router.post("/chat")
async def chat_with_copilot(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Authorized endpoint for merchants to chat with the PointNest AI co-pilot.
    Executes intent routing, read-only MySQL search execution, and returns structured data formats.
    """
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query string cannot be empty."
        )
        
    try:
        # Run co-pilot engine asynchronously
        ai_response = await process_merchant_query(
            db=db,
            query_text=request.query,
            shop_id=current_user.id,
            history=[h.dict() for h in request.history]
        )
        
        return response_parser.success_response(
            message="AI response generated successfully.",
            data=ai_response
        )
    except Exception as e:
        logger.error(f"Error in chat_with_copilot endpoint: {str(e)}")
        raise response_parser.generate_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"PointNest AI experienced a cognitive routing failure: {str(e)}",
            success=False
        )
