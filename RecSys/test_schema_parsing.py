import json

def test_parsing_logic():
    # Mock data matching the new schema
    mock_db_response = [
        {
            "id": 101,
            "product_code": "TEST-001",
            "brand": "TestBrand",
            "name": "Test Product",
            "category_major": "Skincare",
            "category_middle": "Face",
            "category_small": "Serum",
            "price_original": 50000,
            "price_final": 45000,
            "discount_rate": 10,
            "review_score": 4.5,
            "review_count": 100,
            "features": {"texture": "watery"},
            "analytics": {},
            "keywords": "hydrating, soothing"
        },
        {
            "id": 102,
            "product_code": "TEST-002",
            "brand": "TestBrand",
            "name": "Another Product",
            "category_major": "Makeup",
            "category_middle": "Face",
            "category_small": None, # Test missing category
            "price_original": 30000,
            "price_final": 30000,
            "discount_rate": 0,
            "review_score": 4.8,
            "review_count": 50,
            "features": {},
            "analytics": {},
            "keywords": "long-lasting"
        }
    ]

    print("Testing schema parsing logic...")
    
    formatted_products = {}
    for p in mock_db_response:
        # Logic copied from recommendation_model.py
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

    print("\nResult:")
    print(json.dumps(formatted_products, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_parsing_logic()
