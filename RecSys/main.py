from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv
import os
import logging

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache for the recommendation function
_get_recommendation_cached = None
_import_error = None

def load_ml_components():
    """Lazy load heavy ML components to ensure instant server startup"""
    global _get_recommendation_cached, _import_error
    
    if _get_recommendation_cached is not None:
        return _get_recommendation_cached

    logger.info("Deferred loading of ML components started...")
    try:
        # Move heavy imports here
        import torch
        from recommendation_model_API import get_recommendation
        
        logger.info(f"ML components loaded. torch version: {torch.__version__}, GPU available: {torch.cuda.is_available()}")
        _get_recommendation_cached = get_recommendation
        return _get_recommendation_cached
    except Exception as e:
        _import_error = str(e)
        logger.error(f"Error loading ML components: {e}")
        return None

app = FastAPI(
    title="Blooming Recommendation System",
    description="API for recommending products based on user profile",
    version="0.1.0"
)

class RecommendationRequest(BaseModel):
    user_id: str
    target_brand: Optional[List[str]] = []
    intention: Optional[str] = None
    user_data: Optional[Any] = None # Using Any for flexibility during load

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
    # Attempt to load if not already loaded (non-blocking if successful)
    if _get_recommendation_cached is None and _import_error is None:
        # Note: In a real production app, you might want this to be a background task
        # so root always returns instantly. For now, we'll try to load.
        load_ml_components()
        
    return {
        "status": "healthy" if _import_error is None else "error", 
        "service": "Blooming Recommendation System (GPU)",
        "ml_loaded": _get_recommendation_cached is not None,
        "import_error": _import_error,
        "endpoint": "/recommend (POST only)"
    }

@app.get("/health/gpu")
async def health_gpu():
    """Check if GPU is available and return device information"""
    import torch
    gpu_available = torch.cuda.is_available()
    gpu_count = torch.cuda.device_count() if gpu_available else 0
    gpu_name = torch.cuda.get_device_name(0) if gpu_available else "N/A"
    
    return {
        "gpu_available": gpu_available,
        "gpu_count": gpu_count,
        "gpu_name": gpu_name,
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda if gpu_available else "N/A"
    }

@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest):
    """
    Recommend a product based on user profile and history using LLM.
    """
    rec_fn = load_ml_components()
    
    if rec_fn is None:
        raise HTTPException(status_code=500, detail=f"Recommendation engine failed to load: {_import_error}")
        
    try:
        result = await rec_fn(request)
        return result
    except Exception as e:
        logger.error(f"Runtime error in recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    logger.info("Starting RecSys server (main block) on port 80...")
    uvicorn.run("main:app", host="0.0.0.0", port=80)
else:
    logger.info("RecSys app module loaded. ML loading deferred.")
