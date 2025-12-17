import httpx
import asyncio
import json

# 테스트용 고객 데이터 (Case 4: 프로필 + 이력 모두 존재)
mock_payload = {
    "user_id": "user_12345",
    "case": 4,
    "target_brand": ["설화수", "헤라"], # 특정 브랜드 필터링 추가 (리스트)
    "user_data": {
        "user_id": "user_12345",
        "name": "김아모레",
        "age_group": "30s",
        "gender": "F",
        "membership_level": "VVIP",
        "skin_type": ["Dry", "Sensitive"],
        "skin_concerns": ["Wrinkle", "Dullness"],
        "preferred_tone": "Warm_Spring",
        "keywords": ["Vegan", "Clean_Beauty", "Anti-aging"],
        "acquisition_channel": "Instagram_Ad",
        "average_order_value": 150000,
        "average_repurchase_cycle_days": 45,
        "repurchase_cycle_alert": True,
        "last_purchase": {
            "date": "2024-10-01",
            "product_id": "SW-SERUM-001",
            "product_name": "Sulwhasoo First Care Activating Serum"
        },
        "purchase_history": [
            {"brand": "Sulwhasoo", "category": "Serum", "purchase_date": "2024-10-01"},
            {"brand": "Hera", "category": "Lip", "purchase_date": "2024-08-15"}
        ],
        "shopping_behavior": {
            "event_participation": "High",
            "cart_abandonment_rate": "Frequent",
            "price_sensitivity": "Medium"
        },
        "coupon_profile": {
            "history": ["WELCOME_10", "BDAY_2024"],
            "propensity": "Discount_Seeker",
            "preferred_type": "Percentage_Off"
        },
        "last_engagement": {
            "visit_date": "2024-11-20",
            "click_date": "2024-11-20",
            "last_visit_category": "Eye Cream"
        },
        "cart_items": [
            {"id": "HR-CUSHION-02", "name": "Hera Black Cushion", "added_at": "2024-11-19"}
        ],
        "recently_viewed_items": [
            {"id": "SW-CREAM-001", "name": "Sulwhasoo Concentrated Ginseng Cream"},
            {"id": "HR-LIP-002", "name": "Hera Sensual Powder Matte"}
        ]
    }
}

async def test_recommendation():
    print("🚀 추천 시스템 테스트 시작...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8001/recommend", 
                json=mock_payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("\n✅ 추천 결과 수신 성공!")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print(f"\n❌ 오류 발생: {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"\n❌ 연결 실패: {str(e)}")
            print("서버가 실행 중인지 확인해주세요 (cd RecSys && python main.py)")

if __name__ == "__main__":
    asyncio.run(test_recommendation())
