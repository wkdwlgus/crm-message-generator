import os
import json
from typing import Dict, Any, List, Optional
from openai import OpenAI
import httpx
from config import settings

# Global cache for products
PRODUCTS_CACHE = {}

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def fetch_products_from_supabase() -> Dict[str, str]:
    """
    Fetch products from Supabase and format them for the LLM.
    """
    global PRODUCTS_CACHE
    if PRODUCTS_CACHE:
        return PRODUCTS_CACHE

    url = f"{settings.SUPABASE_URL}/rest/v1/products"
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    }

    try:
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(url, headers=headers)
            response.raise_for_status()
            products_data = response.json()
            
            # Format: "ID": "Name (Brand, Category, Description)"
            formatted_products = {}
            for p in products_data:
                # Adjust field names based on actual DB schema
                p_id = p.get("id") or p.get("product_id")
                name = p.get("name") or p.get("product_name")
                brand = p.get("brand", "")
                category = p.get("category", "")
                desc = p.get("description", "")
                
                if p_id and name:
                    info = f"{name} (Brand: {brand}, Category: {category}, {desc})"
                    formatted_products[p_id] = info
            
            PRODUCTS_CACHE = formatted_products
            return formatted_products
            
    except Exception as e:
        print(f"Failed to fetch products from Supabase: {e}")
        # Fallback to empty dict or hardcoded list if needed
        return {}

async def get_recommendation(request_data: Any) -> Dict[str, Any]:
    """
    Get recommendation using OpenAI API based on the case.
    """
    # Fetch products dynamically
    products_db = await fetch_products_from_supabase()
    
    # If DB fetch fails or is empty, use a minimal fallback to prevent crash
    if not products_db:
        products_db = {
            "HR-FOUNDATION-01": "Hera Silky Stay Foundation (Fallback Product)"
        }

    case = request_data.case
    user_data = request_data.user_data
    
    system_prompt = f"""
    You are an expert beauty product recommendation AI.
    You must recommend ONE product from the following list:
    {json.dumps(products_db, indent=2)}
    
    Return the result in JSON format with the following keys:
    - product_id: The ID of the recommended product.
    - score: A confidence score between 0.0 and 1.0.
    - reason: A short explanation of why this product was recommended (in Korean).
    """
    
    user_prompt = ""
    
    if case == 1:
        # Case 1: No data (Cold start)
        user_prompt = "I have no information about this user. Recommend a generally popular best-seller product that works for most people."
        
    elif case == 2:
        # Case 2: History/Context only
        # Extract relevant history fields from user_data
        history_context = {
            "purchase_history": [item.dict() for item in user_data.purchase_history] if user_data else [],
            "shopping_behavior": user_data.shopping_behavior.dict() if user_data else {},
            "cart_items": [item.dict() for item in user_data.cart_items] if user_data else [],
            "recently_viewed_items": [item.dict() for item in user_data.recently_viewed_items] if user_data else [],
            "last_purchase": user_data.last_purchase.dict() if user_data and user_data.last_purchase else None
        }
        
        user_prompt = f"""
        Recommend a product based on the user's past history and behavior context:
        {json.dumps(history_context, indent=2, default=str)}
        
        Key factors to consider:
        - Recent purchases and repurchase cycles
        - Shopping behavior (price sensitivity, cart abandonment)
        - Currently in cart or recently viewed items
        """
        
    elif case == 3:
        # Case 3: Profile only
        if not user_data:
             user_prompt = "User profile is missing. Recommend a popular product."
        else:
            user_prompt = f"""
            Recommend a product based on the user's beauty profile:
            Name: {user_data.name}
            Age Group: {user_data.age_group}
            Gender: {user_data.gender}
            Membership: {user_data.membership_level}
            Skin Type: {', '.join(user_data.skin_type)}
            Skin Concerns: {', '.join(user_data.skin_concerns)}
            Preferred Tone: {user_data.preferred_tone}
            Keywords: {', '.join(user_data.keywords)}
            """
        
    elif case == 4:
        # Case 4: Both Profile and History
        if not user_data:
             user_prompt = "User data is missing. Recommend a popular product."
        else:
            user_prompt = f"""
            Recommend a product based on both the user's detailed profile and behavioral context.
            
            [User Profile]
            Name: {user_data.name}
            Age Group: {user_data.age_group}
            Gender: {user_data.gender}
            Membership: {user_data.membership_level}
            Skin Type: {', '.join(user_data.skin_type)}
            Skin Concerns: {', '.join(user_data.skin_concerns)}
            Preferred Tone: {user_data.preferred_tone}
            Keywords: {', '.join(user_data.keywords)}
            
            [User History & Context]
            {json.dumps(user_data.dict(exclude={'name', 'age_group', 'gender', 'membership_level', 'skin_type', 'skin_concerns', 'preferred_tone', 'keywords'}), indent=2, default=str)}
            
            Comprehensive Analysis Instructions:
            1. Check 'cart_items' and 'recently_viewed_items' for immediate interest.
            2. Check 'repurchase_cycle_alert' to see if they need a refill.
            3. Match 'skin_concerns' and 'keywords' with product benefits.
            4. Consider 'price_sensitivity' and 'average_order_value'.
            5. If they are a 'VVIP', recommend premium lines.
            """
    
    else:
        # Fallback
        user_prompt = "Recommend a popular product."

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Or gpt-3.5-turbo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        content = response.choices[0].message.content
        result = json.loads(content)
        
        # Validate product_id
        if result.get("product_id") not in PRODUCTS_DB:
            # Fallback if LLM hallucinates an ID
            result["product_id"] = "HR-FOUNDATION-01"
            result["reason"] = "기본 추천 상품입니다. (LLM ID 오류)"
            
        return result

    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback in case of error
        return {
            "product_id": "HR-FOUNDATION-01",
            "score": 0.5,
            "reason": "시스템 오류로 인한 기본 추천입니다."
        }
