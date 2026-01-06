
# backend/testdb.py
from supabase import create_client
from config import settings
supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
product_id = "60888"


# 디버깅: legal_info 테이블의 모든 데이터 조회 (최대 5개)
print(f"[Debug] Supabase URL: {settings.SUPABASE_URL}")
print(f"[Debug] product_id type: {type(product_id)}, value: '{product_id}'")

# 테이블 존재 여부 확인 - 전체 데이터 1개만 조회
test_query = supabase.from_("legal_info").select("*").limit(1).execute()
print(f"[Debug] legal_info 테이블 존재 확인: {len(test_query.data)} rows found")
if test_query.data:
    print(f"[Debug] legal_info 샘플 데이터: {test_query.data[0]}")
    print(f"[Debug] product_code 타입: {type(test_query.data[0].get('product_code'))}")

# product_code 컬럼의 모든 값 조회 (디버깅용)
all_codes = supabase.from_("legal_info").select("product_code").limit(10).execute()
print(f"[Debug] legal_info의 product_code 목록 (최대 10개): {[row['product_code'] for row in all_codes.data]}")

print(f"[Info] Supabase legal_info 조회: product_id={product_id}")
result = supabase.from_("legal_info") \
    .select("functional_status, functional_type, all_ingredients, precautions, volume_weight") \
    .eq("product_code", str(product_id)) \
    .execute()

print(f"[Debug] Query result: {result.data}")