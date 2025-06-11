from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from ..core.auth import get_current_user
from ..services.chat_service import process_query
from ..models.chat import ChatQuery, ChatResponse, ChatHistory
from ..core.database import db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/query", response_model=ChatResponse)
async def query_documents(
    query: ChatQuery,
    current_user: dict = Depends(get_current_user)
):
    try:
        logger.info(f"Received query from user {current_user['email']}: {query.text}")
        
        # Process the query using the chat service
        response = await process_query(query.text, str(current_user["_id"]))
        
        # Log the query and response
        chat_history = ChatHistory(
            user_id=str(current_user["_id"]),
            query=query.text,
            response=response["answer"],
            timestamp=datetime.utcnow()
        )
        
        # Save to MongoDB
        await db.chat_history.insert_one(chat_history.dict())
        
        return ChatResponse(
            answer=response["answer"],
            sources=response.get("sources", [])
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )

@router.get("/history", response_model=List[ChatHistory])
async def get_chat_history(
    current_user: dict = Depends(get_current_user)
):
    try:
        # Retrieve chat history for the current user
        history = await db.chat_history.find(
            {"user_id": str(current_user["_id"])}
        ).sort("timestamp", -1).to_list(length=50)
        
        return [ChatHistory(**chat) for chat in history]
    except Exception as e:
        logger.error(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve chat history: {str(e)}"
        )

@router.get("/analytics")
async def get_chat_analytics(
    current_user: dict = Depends(get_current_user)
):
    try:
        # Get frequently asked questions
        pipeline = [
            {"$group": {
                "_id": "$query",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        frequent_queries = await db.chat_history.aggregate(pipeline).to_list(length=None)
        
        # Get total queries count
        total_queries = await db.chat_history.count_documents({})
        
        return {
            "frequent_queries": frequent_queries,
            "total_queries": total_queries
        }
    except Exception as e:
        logger.error(f"Error retrieving analytics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve analytics: {str(e)}"
        ) 