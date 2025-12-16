from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from recommendation_model import get_recommendation
from dotenv import load_dotenv
import os
from models import CustomerProfile

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Blooming Recommendation System",
    description="API for recommending products based on user profile",
    version="0.1.0"
)

class RecommendationRequest(BaseModel):
    user_id: str
    case: int # 1: No data, 2: History only, 3: Profile only, 4: Both
    user_data: Optional[CustomerProfile] = None

class RecommendationResponse(BaseModel):
    product_id: str
    score: float
    reason: str

@app.get("/")
async def root():
    return {"status": "healthy", "service": "Recommendation System"}

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
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
