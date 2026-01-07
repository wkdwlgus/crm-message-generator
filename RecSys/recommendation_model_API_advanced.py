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
                # Schema: id, product_code, brand, name, category_major, category_middle, category_small, 
                # price_original, price_final, discount_rate, review_score, review_count, features, analytics, keywords
                
                p_id = p.get("product_code") or str(p.get("id"))
                name = p.get("name")
                brand = p.get("brand", "")
                
                # Construct category string
                cats = [p.get("category_major"), p.get("category_middle"), p.get("category_small")]
                category = " > ".join([c for c in cats if c])
                
                # Construct description from keywords and features
                keywords = p.get("keywords", "")
                price = p.get("price_final")
                review_score = p.get("review_score")
                
                desc_parts = []
                if keywords:
                    desc_parts.append(f"Keywords: {keywords}")
                if price:
                    desc_parts.append(f"Price: {price}")
                if review_score:
                    desc_parts.append(f"Rating: {review_score}")
                
                desc = ", ".join(desc_parts)
                
                if p_id and name:
                    info = f"{name} (Brand: {brand}, Category: {category}, {desc})"
                    formatted_products[p_id] = info
            
            PRODUCTS_CACHE = formatted_products
            
            # Debug: Print first 3 products to verify format
            print("DEBUG: Sample products from DB:")
            for i, (pid, info) in enumerate(formatted_products.items()):
                if i >= 3: break
                print(f" - {pid}: {info}")
                
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
    print(f"DEBUG: Fetched {len(products_db)} products from DB.")

    # If DB fetch fails or is empty, use a rich mock DB for testing
    if not products_db:
        print("DEBUG: Using mock DB")
        products_db = {
            "SW-SERUM-001": "Sulwhasoo Concentrated Ginseng Renewing Serum (Brand: Sulwhasoo, Category: Serum, Anti-aging, Dry skin)",
            "HR-CUSHION-02": "Hera Black Cushion (Brand: Hera, Category: Makeup, All skin types, Trendy)",
            "HR-FOUNDATION-01": "Hera Silky Stay Foundation (Brand: Hera, Category: Makeup, Long-lasting)",
            "IO-CREAM-003": "IOPE Stem III Cream (Brand: IOPE, Category: Cream, Anti-aging, Repair)",
            "LN-MASK-004": "Laneige Water Sleeping Mask (Brand: Laneige, Category: Mask, Hydration, Night care)",
            "ET-TONER-005": "Etude House SoonJung Toner (Brand: Etude, Category: Toner, Sensitive, Soothing)",
            "IN-CLAY-006": "Innisfree Volcanic Pore Clay Mask (Brand: Innisfree, Category: Mask, Pore care, Oily skin)"
        }

    # Filter by target_brand if provided
    target_brands = getattr(request_data, 'target_brand', None)
    if target_brands:
        filtered_products = {}
        for pid, info in products_db.items():
            # Check if ANY target brand is in the product info
            # Info format: "Name (Brand: BrandName, ...)"
            # We check if any brand in the list is present in the info string
            if any(brand.lower() in info.lower() for brand in target_brands):
                filtered_products[pid] = info
        
        if filtered_products:
            products_db = filtered_products
            print(f"Filtered by brands {target_brands}: {len(products_db)} products found.")
        else:
            print(f"No products found for brands {target_brands}. Using all products.")

    # Limit the number of products to avoid token limits (TPM 30k limit)
    MAX_PRODUCTS = 20
    if len(products_db) > MAX_PRODUCTS:
        print(f"DEBUG: Limiting products from {len(products_db)} to {MAX_PRODUCTS} (Randomly)")
        import random
        # Randomly sample items
        sampled_items = random.sample(list(products_db.items()), MAX_PRODUCTS)
        products_db = dict(sampled_items)

    case = request_data.case
    user_data = request_data.user_data
    
    system_prompt = f"""
    You are an expert beauty product recommendation AI.
    You must recommend ONE product from the following list:
    {json.dumps(products_db, indent=2)}
    
    Return the result in JSON format with the following keys:
    - product_id: The ID of the recommended product.
    - product_name: The exact name of the recommended product.
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
        if result.get("product_id") not in products_db:
            # Fallback if LLM hallucinates an ID
            # Use the first available product ID from the DB
            fallback_id = next(iter(products_db)) if products_db else "HR-FOUNDATION-01"
            result["product_id"] = fallback_id
            # Try to extract name from DB value or use default
            db_val = products_db.get(fallback_id, "Hera Silky Stay Foundation")
            # DB value format: "Name (Brand: ...)"
            result["product_name"] = db_val.split(" (")[0] if " (" in db_val else db_val
            result["reason"] = "기본 추천 상품입니다. (LLM ID 오류)"
            
        return result

    except Exception as e:
        print(f"LLM Error: {e}")
        # Fallback in case of error
        return {
            "product_id": "HR-FOUNDATION-01",
            "product_name": "Hera Silky Stay Foundation",
            "score": 0.5,
            "reason": "시스템 오류로 인한 기본 추천입니다."
        }