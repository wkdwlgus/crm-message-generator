"""
Info Retrieval ↔ RecSys API 연동 테스트
"""
import httpx
import json

# 테스트 설정
BACKEND_URL = "http://localhost:8000"
RECSYS_URL = "http://localhost:8001"

def test_recsys_api_directly():
    """RecSys API 직접 호출 테스트"""
    print("\n" + "="*60)
    print("🧪 테스트 1: RecSys API 직접 호출")
    print("="*60)
    
    # 테스트 페이로드 - 실제 DB에 있는 user_id 사용
    payload = {
        "user_id": "user_0001",
        "case": 4,  # 프로필 + 히스토리
        "target_brand": ["설화수", "헤라"],
        "user_data": None  # RecSys가 DB에서 직접 조회
    }
    
    try:
        # Cross-Encoder 모델 로딩 시간 고려하여 timeout 증가
        with httpx.Client(timeout=120.0) as client:
            print(f"\n📤 요청 URL: {RECSYS_URL}/recommend")
            print(f"📤 User ID: {payload['user_id']}")
            print(f"📤 Case: {payload['case']}")
            print(f"📤 Target Brands: {payload['target_brand']}")
            print(f"⏱️  첫 요청은 모델 로딩으로 시간이 걸릴 수 있습니다...")
            
            response = client.post(f"{RECSYS_URL}/recommend", json=payload)
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✅ RecSys API 응답 성공!")
            print(f"📦 Response Keys: {list(result.keys())}")
            print(f"\n🎯 추천 상품:")
            print(f"  - Product ID: {result.get('product_id')}")
            print(f"  - Product Name: {result.get('product_name')}")
            print(f"  - Score: {result.get('score'):.4f}")
            print(f"  - Reason: {result.get('reason')}")
            
            if 'product_data' in result and result['product_data']:
                print(f"\n📊 상세 정보:")
                pd = result['product_data']
                print(f"  - Brand: {pd.get('brand')}")
                print(f"  - Name: {pd.get('name')}")
                print(f"  - Price: {pd.get('price', {}).get('discounted_price', 0):,}원")
                print(f"  - Review Score: {pd.get('review', {}).get('score')}")
            else:
                print(f"\n⚠️ product_data가 없거나 비어있음")
            
            return True
            
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backend_message_api():
    """Backend 메시지 생성 API 테스트 (info_retrieval 포함)"""
    print("\n" + "="*60)
    print("🧪 테스트 2: Backend 메시지 생성 API (전체 플로우)")
    print("="*60)
    
    # 테스트 페이로드 - 실제 DB에 있는 user_id 사용
    payload = {
        "user_id": "user_0001",
        "channel": "SMS"
    }
    
    try:
        with httpx.Client(timeout=120.0) as client:  # 충분한 타임아웃
            print(f"\n📤 요청 URL: {BACKEND_URL}/api/message")
            print(f"📤 User ID: {payload['user_id']}")
            print(f"📤 Channel: {payload['channel']}")
            print(f"⏱️  전체 워크플로우 실행 중...")
            
            # GET 요청으로 변경 (헤더로 user_id 전달)
            response = client.get(
                f"{BACKEND_URL}/api/message",
                headers={"X-User-Id": payload["user_id"]},
                params={"channel": payload["channel"]}
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✅ Backend API 응답 성공!")
            print(f"\n📝 생성된 메시지:")
            print(f"  Message: {result.get('message')}")
            print(f"\n📊 메타 정보:")
            print(f"  - Success: {result.get('success')}")
            print(f"  - User ID: {result.get('user_id')}")
            print(f"  - Channel: {result.get('channel')}")
            
            if 'product_data' in result:
                print(f"\n🛍️ 추천 상품:")
                pd = result['product_data']
                print(f"  - Product ID: {pd.get('product_id')}")
                print(f"  - Brand: {pd.get('brand')}")
                print(f"  - Name: {pd.get('name')}")
            
            return True
            
    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        print(f"Response: {e.response.text}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_server_health():
    """서버 헬스체크"""
    print("\n" + "="*60)
    print("🏥 서버 헬스 체크")
    print("="*60)
    
    servers = [
        ("Backend (8000)", f"{BACKEND_URL}/"),
        ("RecSys (8001)", f"{RECSYS_URL}/"),
    ]
    
    results = []
    for name, url in servers:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(url)
                if response.status_code == 200:
                    print(f"✅ {name}: OK")
                    results.append(True)
                else:
                    print(f"⚠️ {name}: Status {response.status_code}")
                    results.append(False)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append(False)
    
    return all(results)


if __name__ == "__main__":
    print("\n" + "🚀 Info Retrieval ↔ RecSys 연동 테스트 시작" + "\n")
    
    # 1. 헬스체크
    if not test_server_health():
        print("\n❌ 서버가 정상적으로 실행되지 않았습니다.")
        print("Backend: uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        print("RecSys: python main.py (포트 8001)")
        exit(1)
    
    # 2. RecSys API 직접 테스트
    test1_result = test_recsys_api_directly()
    
    # 3. Backend 전체 플로우 테스트
    test2_result = test_backend_message_api()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과 요약")
    print("="*60)
    print(f"RecSys API 직접 호출: {'✅ 성공' if test1_result else '❌ 실패'}")
    print(f"Backend 전체 플로우: {'✅ 성공' if test2_result else '❌ 실패'}")
    
    if test1_result and test2_result:
        print("\n🎉 모든 테스트 통과! 연동이 정상적으로 작동합니다.")
    else:
        print("\n⚠️ 일부 테스트 실패. 로그를 확인해주세요.")
