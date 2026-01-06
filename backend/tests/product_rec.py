import os
from typing import Any, Dict, List, Tuple

from supabase import create_client
from openai import OpenAI

# Cross-Encoder (reranker)
from sentence_transformers import CrossEncoder
import torch

# backend 폴더를 path에 먼저 추가 (venv의 config 패키지보다 우선)
from pathlib import Path
import sys
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from config import settings

# =========================
# 테스트할 유저 리스트 (요청 그대로)
# =========================
USER_IDS = ["user_0001", "user_0002.", "user_0003.", "user_0004.", "user_0005."]

# 최종 출력 topK
TOP_K = 3

# 벡터 후보 풀 (여기 크게!)
CANDIDATE_POOL = 200

# Embedding
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

# Cross-Encoder 모델 (멀티링구얼 reranker)
CE_MODEL = "BAAI/bge-reranker-v2-m3"

# B) 키워드 보너스 강도
KW_BONUS_ALPHA = 1.2  # ce_score에 더해질 보너스 가중치 (0.5~2.0 사이로 튜닝 추천)

# customers에서 USER_ID를 조회할 컬럼명
CUSTOMER_ID_COL = "user_id"

# products_vector에서 product_id를 조회할 컬럼명
PRODUCT_VECTOR_FK_COL = "product_id"


# =========================
# 성능용 동의어 매핑
# =========================
SKIN_TYPE_MAP = {
    "Sensitive": "민감성",
    "Dry": "건성",
    "Oily": "지성",
    "Combination": "복합성",
    "Neutral": "중성",
    "Normal": "중성",
}

CONCERN_MAP = {
    "Pores": "모공",
    "Sebum": "피지",
    "Acne": "여드름",
    "Redness": "홍조",
    "Dryness": "건조",
    "Wrinkle": "주름",
    "Elasticity": "탄력",
    "Dullness": "칙칙함",
    "Anti-aging": "안티에이징",
    "Antiaging": "안티에이징",
    "Sensitive": "민감",
    "Sensitivity": "민감",
}

TONE_MAP = {
    "Cool_Summer": "쿨톤 여름",
    "Cool_Winter": "쿨톤 겨울",
    "Warm_Spring": "웜톤 봄",
    "Warm_Autumn": "웜톤 가을",
    "Neutral": "뉴트럴",
}


def normalize_list(v: Any) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    # text[]가 "{a,b}" 문자열로 오는 경우 대비
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1]
        return [x.strip().strip('"') for x in s.split(",") if x.strip()]
    return [str(v).strip()]


def with_kr(items: List[str], mapping: Dict[str, str]) -> List[str]:
    out = []
    for x in items:
        k = mapping.get(x)
        out.append(f"{x}({k})" if k else x)
    return out


# =========================
# A) "키워드 최우선" 쿼리 텍스트 (Cross-Encoder용)
# =========================
def build_user_query_text(customer: Dict[str, Any]) -> str:
    skin_types = with_kr(normalize_list(customer.get("skin_type")), SKIN_TYPE_MAP)
    concerns = with_kr(normalize_list(customer.get("skin_concerns")), CONCERN_MAP)
    keywords = normalize_list(customer.get("keywords"))
    tone = customer.get("preferred_tone")
    tone_kr = TONE_MAP.get(tone, tone) if tone else None

    # ✅ 키워드를 최상단에 배치 + "최우선" 라벨 + 1회 재강조
    lines = [
        "스킨케어 제품 추천 쿼리 (키워드 최우선)",
        "",
        "[중요 키워드 TOP - 최우선 반영]",
        f"- {', '.join(keywords)}" if keywords else "- (없음)",
        "※ 위 키워드와 직접적으로 연결되는 효능/특징/제품 키워드가 포함된 제품을 최우선으로 평가한다.",
        "",
        "[피부타입]",
        f"- {', '.join(skin_types)}" if skin_types else "- 정보 없음",
        "",
        "[피부고민]",
        f"- {', '.join(concerns)}" if concerns else "- 정보 없음",
        "",
        "[추구 톤]",
        f"- {tone_kr}" if tone_kr else "- 정보 없음",
        "",
        "[평가 기준 재강조]",
        f"- 핵심 키워드({', '.join(keywords)})와 연관성이 높은 제품을 우선 추천" if keywords else "- 키워드 기반 우선 추천",
    ]
    return "\n".join(lines)


def embed_text(oa: OpenAI, text: str) -> List[float]:
    res = oa.embeddings.create(
        model=EMBED_MODEL,
        input=[text],
        encoding_format="float",
    )
    emb = res.data[0].embedding
    if len(emb) != EMBED_DIM:
        raise ValueError(f"임베딩 차원 불일치: got {len(emb)} expected {EMBED_DIM}")
    return emb


def safe_preview(text: str, max_len: int = 800) -> str:
    text = text or ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated) ..."


def truncate_for_ce(text: str, max_chars: int = 1800) -> str:
    # CE 입력 길이 폭주 방지 (너무 길면 오히려 성능/속도 나빠짐)
    text = text or ""
    return text if len(text) <= max_chars else text[:max_chars]


# =========================
# B) 키워드 매칭 보너스
# - user_keywords가 product_content에 얼마나 "직접" 나타나는지 점수화 (0~1)
# - "키워드:" 라인에 있으면 더 가산 (구조화 데이터에 더 신뢰 부여)
# =========================
def keyword_bonus(user_keywords: List[str], product_content: str) -> float:
    kws = [k.strip() for k in (user_keywords or []) if k and str(k).strip()]
    if not kws:
        return 0.0

    text = (product_content or "").lower()
    # content 안에 "키워드:" 줄이 있을 때 거기만 따로 더 가중
    keyword_line = ""
    for line in (product_content or "").splitlines():
        if "키워드" in line:
            keyword_line = line.lower()
            break

    hit_any = 0
    hit_kwline = 0
    for kw in kws:
        k = kw.lower()
        if k in text:
            hit_any += 1
        if keyword_line and k in keyword_line:
            hit_kwline += 1

    # 0~1 사이 정규화
    # "키워드 라인 히트"를 더 크게 반영
    score = (2.0 * hit_kwline + 1.0 * hit_any) / (3.0 * max(len(kws), 1))
    return float(min(1.0, max(0.0, score)))


def load_cross_encoder():
    # GPU 있으면 자동 사용
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n[CrossEncoder] loading: {CE_MODEL} on device={device}")
    return CrossEncoder(CE_MODEL, device=device)


def run_for_user(sb, oa, ce: CrossEncoder, user_id: str):
    print("\n" + "=" * 90)
    print(f"USER_ID = {user_id}")
    print("=" * 90)

    # 1) 고객 정보 조회
    customer_resp = (
        sb.table("customers")
        .select("user_id, skin_type, skin_concerns, keywords, preferred_tone")
        .eq(CUSTOMER_ID_COL, user_id)
        .limit(1)
        .execute()
    )

    if not customer_resp.data:
        print(f"[SKIP] customers에서 {CUSTOMER_ID_COL}={user_id} 를 찾지 못함")
        return

    customer = customer_resp.data[0]
    user_keywords = normalize_list(customer.get("keywords"))

    print("\n[customer raw]")
    print("user_id:", customer.get("user_id"))
    print("skin_type:", customer.get("skin_type"))
    print("skin_concerns:", customer.get("skin_concerns"))
    print("keywords:", customer.get("keywords"))
    print("preferred_tone:", customer.get("preferred_tone"))

    # 2) 질의문 생성 (A 적용)
    query_text = build_user_query_text(customer)
    print("\n[query_text]")
    print(query_text)

    # 3) 임베딩 생성 (후보 풀용)
    query_emb = embed_text(oa, query_text)

    # 4) RPC 유사도 검색 (후보 풀 크게!)
    rpc_payload = {
        "filter": {},
        "match_count": CANDIDATE_POOL,
        "query_embedding": query_emb,
    }
    match_resp = sb.rpc("match_products", rpc_payload).execute()
    matches = match_resp.data or []

    if not matches:
        print("\n[RESULT] 유사도 검색 결과가 없습니다.")
        return

    # 벡터 similarity 높은 순으로 일단 정렬
    matches.sort(key=lambda m: float(m.get("similarity", 0.0)), reverse=True)

    candidate_ids = [m["product_id"] for m in matches]
    sim_map = {m["product_id"]: float(m["similarity"]) for m in matches}

    # 5) products 상세 (후보 풀 전부 가져오기)
    products_resp = (
        sb.table("products")
        .select("id, brand, name, category_major, category_middle, category_small, price_final, discount_rate, review_score, review_count")
        .in_("id", candidate_ids)
        .execute()
    )
    products = products_resp.data or []
    prod_map = {p["id"]: p for p in products}

    # 6) products_vector content 가져오기
    pv_resp = (
        sb.table("products_vector")
        .select(f"{PRODUCT_VECTOR_FK_COL}, content")
        .in_(PRODUCT_VECTOR_FK_COL, candidate_ids)
        .execute()
    )
    pv_rows = pv_resp.data or []
    pv_map = {r[PRODUCT_VECTOR_FK_COL]: r.get("content") for r in pv_rows}

    # 7) Cross-Encoder rerank + B) keyword bonus 합산
    # CE 입력: (query_text, product_content)
    pairs: List[Tuple[str, str]] = []
    valid_ids: List[int] = []

    for pid in candidate_ids:
        content = pv_map.get(pid)
        if not content:
            continue
        valid_ids.append(pid)
        pairs.append((truncate_for_ce(query_text), truncate_for_ce(content)))

    if not pairs:
        print("\n[RESULT] 후보의 products_vector.content가 비어있습니다.")
        return

    ce_scores = ce.predict(pairs)  # float list

    reranked = []
    for pid, ce_score in zip(valid_ids, ce_scores):
        content = pv_map.get(pid, "")
        kwb = keyword_bonus(user_keywords, content)  # 0~1
        final_score = float(ce_score) + KW_BONUS_ALPHA * kwb
        reranked.append(
            {
                "product_id": pid,
                "ce_score": float(ce_score),
                "kw_bonus": float(kwb),
                "final_score": float(final_score),
                "similarity": float(sim_map.get(pid, 0.0)),
            }
        )

    reranked.sort(key=lambda r: r["final_score"], reverse=True)
    top = reranked[:TOP_K]

    print(f"\n[TOP {TOP_K} RECOMMENDATIONS] (Cross-Encoder reranked + keyword bonus)")
    for rank, row in enumerate(top, start=1):
        pid = row["product_id"]
        p = prod_map.get(pid)
        content = pv_map.get(pid, "")

        if not p:
            print(f"\n{rank:02d}. final={row['final_score']:.6f} | ce={row['ce_score']:.6f} | kwb={row['kw_bonus']:.3f} | sim={row['similarity']:.6f} | product_id={pid}")

            continue

        cat = " > ".join([c for c in [p.get("category_major"), p.get("category_middle"), p.get("category_small")] if c])

        print(
            f"\n{rank:02d}. final={row['final_score']:.6f} | ce={row['ce_score']:.6f} | kwb={row['kw_bonus']:.3f} | sim={row['similarity']:.6f} "
            f"[{p.get('brand','')}] {p.get('name','')}"
        )
        print(f"    category: {cat}")
        print(f"    price_final: {p.get('price_final')} | discount_rate: {p.get('discount_rate')}")
        print(f"    review: {p.get('review_score')} ({p.get('review_count')})")



def main():
    sb_url = settings.SUPABASE_URL
    sb_key = settings.SUPABASE_KEY
    oa_key = settings.openai_api_key

    sb = create_client(sb_url, sb_key)
    oa = OpenAI(api_key=oa_key)

    # Cross-Encoder는 한 번만 로드해서 재사용
    ce = load_cross_encoder()

    for uid in USER_IDS:
        run_for_user(sb, oa, ce, uid)


if __name__ == "__main__":
    main()
