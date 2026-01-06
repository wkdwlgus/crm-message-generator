import asyncio
import os
from recommendation_model_API import get_recommendation
from models import CustomerProfile, PurchaseHistoryItem, ShoppingBehavior, CartItem, RecentlyViewedItem, LastPurchase
from pydantic import BaseModel
from typing import Optional, List

class RecommendationRequest(BaseModel):
    user_id: str
    case: int
    target_brand: Optional[List[str]] = None
    user_data: Optional[CustomerProfile] = None

async def test_rec():
    print("Testing get_recommendation...")
    
    # Mock request data for Case 1 (simplest) with Brand Filter
    req = RecommendationRequest(
        user_id="test_user",
        case=1,
        target_brand=["헤라", "설화수"],
        user_data=None
    )
    
    try:
        result = await get_recommendation(req)
        print("Result:", result)
    except Exception as e:
        print(f"Error calling get_recommendation: {e}")
    print("Done.")

if __name__ == "__main__":
    asyncio.run(test_rec())
