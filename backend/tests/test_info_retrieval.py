"""
info_retrieval.py 테스트 스크립트
recommend_product_with_brands 함수를 직접 테스트
"""
import sys
from pathlib import Path

# backend 폴더를 path에 추가
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from actions.info_retrieval import recommend_product_with_brands

# 테스트할 유저 ID와 브랜드 리스트
TEST_USER_ID = "user_0001"
TEST_BRANDS = [ "설화수", "헤라"]  # 원하는 브랜드로 수정

def test_recommend_product_with_brands():
    """브랜드 필터링 상품 추천 테스트"""
    print("\n" + "=" * 90)
    print(f"브랜드 필터링 상품 추천 테스트")
    print(f"USER_ID: {TEST_USER_ID}")
    print(f"TARGET_BRANDS: {TEST_BRANDS}")
    print("=" * 90)
    
    result = recommend_product_with_brands(
        user_id=TEST_USER_ID,
        target_brands=TEST_BRANDS,
        top_k=1
    )
    
    if result:
        print("\n✅ 추천 성공!")
        print(f"Product ID: {result['product_id']}")
        print(f"Brand: {result['brand']}")
        print(f"Name: {result['name']}")
        print(f"Category: {result['category_major']} > {result['category_middle']} > {result['category_small']}")
        print(f"Price: {result['price_final']}원")
        print(f"Discount Rate: {result['discount_rate']}%")
        print(f"Review: {result['review_score']}점 ({result['review_count']}개)")
        print(f"\n📊 Scores:")
        print(f"  - CE Score: {result['ce_score']:.6f}")
        print(f"  - Keyword Bonus: {result['kw_bonus']:.4f}")
        print(f"  - Final Score: {result['final_score']:.6f}")
        print(f"  - Similarity: {result['similarity']:.6f}")
    else:
        print("\n❌ 추천 실패")


def test_multiple_users():
    """여러 유저 테스트"""
    users = ["user_0001", "user_0002", "user_0003"]
    
    for user_id in users:
        print("\n" + "=" * 90)
        print(f"USER_ID: {user_id}")
        print("=" * 90)
        
        result = recommend_product_with_brands(
            user_id=user_id,
            target_brands=TEST_BRANDS,
            top_k=1
        )
        
        if result:
            print(f"✅ [{result['brand']}] {result['name']} (Score: {result['final_score']:.4f})")
        else:
            print(f"❌ 추천 실패")


if __name__ == "__main__":
    # 단일 유저 테스트
    test_recommend_product_with_brands()
    
    # 여러 유저 테스트 (원하면 주석 해제)
    # test_multiple_users()
