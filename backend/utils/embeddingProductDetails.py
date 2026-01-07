import os
import json
import time
from typing import Any, Dict, List, Optional
import sys
from pathlib import Path

from supabase import create_client, Client
from openai import OpenAI

# backend 폴더를 path에 먼저 추가 (venv의 config 패키지보다 우선)
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings

# =========================
# 설정
# =========================
EMBEDDING_MODEL = "text-embedding-3-small"  # 보통 1536-dim
EMBEDDING_DIM = 1536                       # products_vector의 vector(n)과 일치해야 함

PAGE_SIZE = 200                            # products에서 읽어오는 단위
EMBED_BATCH_SIZE = 100                     # OpenAI 임베딩 요청 배치 크기
SLEEP_BETWEEN_PAGES = 0.1                  # 너무 빠르면 DB/네트워크 부담될 수 있어 약간 쉬기

# products_vector 테이블의 PK 컬럼명 (보통 product_id)
VECTOR_PK_COL = "product_id"

# =========================
# 유틸
# =========================
def safe_json_parse(value: Any, fallback: Any):
    """features/analytics/keywords가 str(JSON)일 수도 있고 이미 dict/list일 수도 있어서 안전 파싱."""
    if value is None:
        return fallback
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return fallback
    return fallback


def pick_arrays(obj: Dict[str, Any], keys: List[str]) -> List[str]:
    out = []
    for k in keys:
        v = obj.get(k)
        if isinstance(v, list):
            out.extend([str(x) for x in v if x])
    return out


def build_embedding_text(p: Dict[str, Any]) -> str:
    """
    제품 row -> 임베딩용 자연어 content 생성
    (의미/취향 유사도에 도움 되는 텍스트만 최대한 모음)
    """
    features = safe_json_parse(p.get("features"), {})
    keywords = safe_json_parse(p.get("keywords"), [])
    analytics = safe_json_parse(p.get("analytics"), {})

    # features에서 텍스트로 의미 있는 것들만 쭉 모으기
    feature_lines = []
    feature_lines += pick_arrays(features, ["key_points", "visual_concept", "technology_ingredients"])
    feature_lines += pick_arrays(features, ["efficacy_data", "reliability"])
    feature_lines += pick_arrays(features, ["emotional_benefits"])
    feature_lines += pick_arrays(features, ["texture", "scent"])
    feature_lines += pick_arrays(features, ["usage"])

    analytics_lines = []
    if analytics.get("skin_type"):
        analytics_lines.append(f"피부타입: {analytics['skin_type']}")
    if analytics.get("age_group"):
        analytics_lines.append(f"연령대: {analytics['age_group']}")

    category_path = " > ".join(
        [x for x in [p.get("category_major"), p.get("category_middle"), p.get("category_small")] if x]
    )

    lines = [
        f"브랜드: {p.get('brand', '')}",
        f"제품명: {p.get('name', '')}",
        f"카테고리: {category_path}" if category_path else None,
        f"키워드: {', '.join(keywords)}" if isinstance(keywords, list) and len(keywords) else None,
        f"특징: {' | '.join(feature_lines)}" if len(feature_lines) else None,
        f"타겟/피부정보: {', '.join(analytics_lines)}" if len(analytics_lines) else None,
    ]

    # None 제거 후 합치기
    return "\n".join([x for x in lines if x])


def build_metadata(p: Dict[str, Any]) -> Dict[str, Any]:
    """
    벡터 검색 이후 룰베이스 필터/정렬/재랭킹에 유용한 숫자/카테고리 저장.
    """
    return {
        "brand": p.get("brand"),
        "category_major": p.get("category_major"),
        "category_middle": p.get("category_middle"),
        "category_small": p.get("category_small"),
        "price_final": p.get("price_final"),
        "discount_rate": p.get("discount_rate"),
        "review_score": p.get("review_score"),
        "review_count": p.get("review_count"),
        "benefit_discount_rate": p.get("benefit_discount_rate"),
        "price_benefit": p.get("price_benefit"),
    }


def chunk_list(items: List[Any], size: int) -> List[List[Any]]:
    return [items[i:i + size] for i in range(0, len(items), size)]


def embed_texts(openai_client: OpenAI, texts: List[str], max_retries: int = 5) -> List[List[float]]:
    """
    OpenAI embeddings 호출 (재시도 포함)
    """
    for attempt in range(1, max_retries + 1):
        try:
            res = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
                encoding_format="float",
                # dimensions=768,  # 차원 줄이면 DB vector(n)도 n에 맞게 바꿔야 함
            )
            vectors = [d.embedding for d in res.data]
            return vectors
        except Exception as e:
            if attempt == max_retries:
                raise
            wait = 2 ** attempt
            print(f"[WARN] embedding 실패, {wait}s 후 재시도 ({attempt}/{max_retries}) - {e}")
            time.sleep(wait)

    raise RuntimeError("embedding 재시도 실패")


# =========================
# 메인 로직
# =========================
def main():
    supabase_url = settings.SUPABASE_URL
    supabase_key = settings.SUPABASE_KEY
    openai_key = settings.openai_api_key

    sb: Client = create_client(supabase_url, supabase_key)
    oa = OpenAI(api_key=openai_key)

    offset = 0
    total_processed = 0

    while True:
        # 1) products 페이지 단위로 읽기
        resp = (
            sb.table("products")
            .select(
                "id, product_code, brand, name, category_major, category_middle, category_small,"
                "features, analytics, keywords,"
                "price_original, price_final, discount_rate, review_score, review_count,"
                "price_benefit, benefit_discount_rate"
            )
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )

        products = resp.data or []
        if not products:
            print("✅ 모든 products 처리 완료")
            break

        # 2) content 만들기
        contents = [build_embedding_text(p) for p in products]

        # 3) 임베딩은 배치로 나눠서 호출
        all_vectors: List[List[float]] = []
        for batch in chunk_list(contents, EMBED_BATCH_SIZE):
            vectors = embed_texts(oa, batch)
            all_vectors.extend(vectors)

        # 4) upsert payload 구성
        upserts = []
        for p, content, emb in zip(products, contents, all_vectors):
            if len(emb) != EMBEDDING_DIM:
                raise ValueError(f"임베딩 차원 불일치: got {len(emb)}, expected {EMBEDDING_DIM}")

            upserts.append({
                VECTOR_PK_COL: p["id"],          # products.id -> products_vector.product_id
                "content": content,
                "embedding": emb,               # vector 컬럼에 list[float] 넣기
                "metadata": build_metadata(p),
            })

        # 5) products_vector에 upsert
        #    on_conflict는 PK 컬럼명과 동일해야 함
        upsert_resp = (
            sb.table("products_vector")
            .upsert(upserts, on_conflict=VECTOR_PK_COL)
            .execute()
        )

        total_processed += len(products)
        offset += PAGE_SIZE

        print(f"✅ upsert 완료: 이번 {len(products)}개 / 누적 {total_processed}개")

        time.sleep(SLEEP_BETWEEN_PAGES)

    print("🎉 전체 임베딩 적재 완료")


if __name__ == "__main__":
    main()
