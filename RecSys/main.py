from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv
import os
import torch
from models import CustomerProfile

# Load environment variables
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing FastAPI app...")
get_recommendation = None # Placeholder

try:
    from recommendation_model_API import get_recommendation
    logger.info("Imported recommendation_model_API successfully")
except Exception as e:
    logger.error(f"Error importing recommendation_model_API: {e}")

app = FastAPI(
    title="Blooming Recommendation System",
    description="API for recommending products based on user profile",
    version="0.1.0"
)

class RecommendationRequest(BaseModel):
    user_id: str
    target_brand: Optional[List[str]] = [] # Target brand list
    intention: Optional[str] = None # Recommendation intention (ex: "weather", "new_product", "general")
    user_data: Optional[CustomerProfile] = None

class RecommendationResponse(BaseModel):
    product_id: str
    product_name: str
    score: float
    reason: str
    product_data: Optional[Dict[str, Any]] = None

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)

@app.get("/")
async def root():
    return {
        "status": "healthy", 
        "service": "Blooming Recommendation System (GPU)",
        "endpoint": "/recommend (POST only)"
    }

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Recommend a product based on user profile and history using LLM.
    """
    try:
        result = await get_recommendation(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # This block is for local development
    import uvicorn
    logger.info("Starting RecSys server (main block) on port 80...")
    uvicorn.run("main:app", host="0.0.0.0", port=80)
else:
    # This block runs when imported (e.g., by uvicorn worker in Docker)
    logger.info("RecSys app module loaded")
