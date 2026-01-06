import os
import json
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
import httpx
from config import settings
from supabase import create_client
from sentence_transformers import CrossEncoder
import torch

# Cross-Encoder 설정
TOP_K = 3
CANDIDATE_POOL = 200
EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
CE_MODEL = "BAAI/bge-reranker-v2-m3"
KW_BONUS_ALPHA = 1.2
CUSTOMER_ID_COL = "user_id"
PRODUCT_VECTOR_FK_COL = "product_id"

# 동의어 매핑
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

# Cross-Encoder 캐싱 (한 번만 로드)
_cross_encoder_cache = None

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_cross_encoder() -> CrossEncoder:
    """Cross-Encoder를 로드하거나 캐시된 인스턴스 반환"""
    global _cross_encoder_cache
    if _cross_encoder_cache is None:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[CrossEncoder] loading: {CE_MODEL} on device={device}")
        _cross_encoder_cache = CrossEncoder(CE_MODEL, device=device)
    return _cross_encoder_cache


def normalize_list(v: Any) -> List[str]:
    """리스트 정규화"""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("{") and s.endswith("}"):
            s = s[1:-1]
        return [x.strip().strip('"') for x in s.split(",") if x.strip()]
    return [str(v).strip()]


def with_kr(items: List[str], mapping: Dict[str, str]) -> List[str]:
    """영어 키워드에 한글 매핑 추가"""
    out = []
    for x in items:
        k = mapping.get(x)
        out.append(f"{x}({k})" if k else x)
    return out


def build_user_query_text(customer: Dict[str, Any]) -> str:
    """유저 정보를 기반으로 쿼리 텍스트 생성"""
    skin_types = with_kr(normalize_list(customer.get("skin_type")), SKIN_TYPE_MAP)
    concerns = with_kr(normalize_list(customer.get("skin_concerns")), CONCERN_MAP)
    keywords = normalize_list(customer.get("keywords"))
    tone = customer.get("preferred_tone")
    tone_kr = TONE_MAP.get(tone, tone) if tone else None

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
    """텍스트를 임베딩 벡터로 변환"""
    res = oa.embeddings.create(
        model=EMBED_MODEL,
        input=[text],
        encoding_format="float",
    )
    emb = res.data[0].embedding
    if len(emb) != EMBED_DIM:
        raise ValueError(f"임베딩 차원 불일치: got {len(emb)} expected {EMBED_DIM}")
    return emb


def truncate_for_ce(text: str, max_chars: int = 1800) -> str:
    """Cross-Encoder 입력 길이 제한"""
    text = text or ""
    return text if len(text) <= max_chars else text[:max_chars]


def keyword_bonus(user_keywords: List[str], product_content: str) -> float:
    """키워드 매칭 보너스 계산 (0~1)"""
    kws = [k.strip() for k in (user_keywords or []) if k and str(k).strip()]
    if not kws:
        return 0.0

    text = (product_content or "").lower()
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

    score = (2.0 * hit_kwline + 1.0 * hit_any) / (3.0 * max(len(kws), 1))
    return float(min(1.0, max(0.0, score)))


async def fetch_products_from_supabase() -> Dict[str, str]:
    """
    Fetch products from Supabase and format them for the LLM.
    (Deprecated - 이제 recommend_product_with_brands 사용)
    """
    return {}

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
            full_data = {}  # Store full product data
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
                    # Store full product data
                    full_data[p_id] = p
            
            PRODUCTS_CACHE = formatted_products
            PRODUCTS_FULL_DATA = full_data
            
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

async def recommend_product_with_brands(
    user_id: str,
    user_data: Any,
    target_brands: List[str] = None,
    top_k: int = 1
) -> Optional[Dict[str, Any]]:
    """
    유저 ID와 브랜드 리스트를 받아 Cross-Encoder 기반으로 최고의 상품을 추천합니다.
    
    Args:
        user_id: 사용자 ID
        user_data: CustomerProfile 객체 (user_data에서 추출한 정보)
        target_brands: 추천할 브랜드 리스트 (None이면 모든 브랜드)
        top_k: 반환할 상품 개수 (기본값: 1)
        
    Returns:
        추천 상품 정보 dict 또는 None
    """
    try:
        # Supabase 및 OpenAI 클라이언트 초기화
        sb = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        oa = OpenAI(api_key=settings.OPENAI_API_KEY)
        ce = get_cross_encoder()
        
        # 1) 고객 정보 조회
        customer_resp = (
            sb.table("customers")
            .select("user_id, skin_type, skin_concerns, keywords, preferred_tone")
            .eq(CUSTOMER_ID_COL, user_id)
            .limit(1)
            .execute()
        )
        
        if not customer_resp.data:
            print(f"[WARN] customers에서 {CUSTOMER_ID_COL}={user_id}를 찾지 못함")
            return None
        
        customer = customer_resp.data[0]
        user_keywords = normalize_list(customer.get("keywords"))
        
        # 2) 쿼리 텍스트 생성
        query_text = build_user_query_text(customer)
        
        # 3) 임베딩 생성
        query_emb = embed_text(oa, query_text)
        
        # 4) 벡터 유사도 검색 (후보 풀)
        rpc_payload = {
            "filter": {},
            "match_count": CANDIDATE_POOL,
            "query_embedding": query_emb,
        }
        match_resp = sb.rpc("match_products", rpc_payload).execute()
        matches = match_resp.data or []
        
        if not matches:
            print("[WARN] 유사도 검색 결과가 없습니다.")
            return None
        
        matches.sort(key=lambda m: float(m.get("similarity", 0.0)), reverse=True)
        candidate_ids = [m["product_id"] for m in matches]
        sim_map = {m["product_id"]: float(m["similarity"]) for m in matches}
        
        # 5) products 상세 정보 조회 (브랜드 필터링 적용)
        query = (
            sb.table("products")
            .select("id, brand, name, category_major, category_middle, category_small, price_final, discount_rate, review_score, review_count")
            .in_("id", candidate_ids)
        )
        
        if target_brands and len(target_brands) > 0:
            query = query.in_("brand", target_brands)
            print(f"  🏷️ 브랜드 필터링 적용: {target_brands}")
        
        products_resp = query.execute()
        products = products_resp.data or []
        
        if not products:
            if target_brands:
                print(f"[WARN] 지정된 브랜드({target_brands})에서 상품을 찾지 못함")
            else:
                print("[WARN] 상품을 찾지 못함")
            return None
        
        prod_map = {p["id"]: p for p in products}
        filtered_ids = list(prod_map.keys())
        
        # 6) products_vector content 가져오기
        pv_resp = (
            sb.table("products_vector")
            .select(f"{PRODUCT_VECTOR_FK_COL}, content")
            .in_(PRODUCT_VECTOR_FK_COL, filtered_ids)
            .execute()
        )
        pv_rows = pv_resp.data or []
        pv_map = {r[PRODUCT_VECTOR_FK_COL]: r.get("content") for r in pv_rows}
        
        # 7) Cross-Encoder rerank + keyword bonus
        pairs: List[Tuple[str, str]] = []
        valid_ids: List[int] = []
        
        for pid in filtered_ids:
            content = pv_map.get(pid)
            if not content:
                continue
            valid_ids.append(pid)
            pairs.append((truncate_for_ce(query_text), truncate_for_ce(content)))
        
        if not pairs:
            print("[WARN] 브랜드 필터링 후 products_vector.content가 비어있습니다.")
            return None
        
        ce_scores = ce.predict(pairs)
        
        reranked = []
        for pid, ce_score in zip(valid_ids, ce_scores):
            content = pv_map.get(pid, "")
            kwb = keyword_bonus(user_keywords, content)
            final_score = float(ce_score) + KW_BONUS_ALPHA * kwb
            p = prod_map.get(pid)
            
            reranked.append({
                "product_id": str(pid),
                "brand": p.get("brand"),
                "name": p.get("name"),
                "category_major": p.get("category_major"),
                "category_middle": p.get("category_middle"),
                "category_small": p.get("category_small"),
                "price_final": p.get("price_final"),
                "discount_rate": p.get("discount_rate"),
                "review_score": p.get("review_score"),
                "review_count": p.get("review_count"),
                "ce_score": float(ce_score),
                "kw_bonus": float(kwb),
                "final_score": float(final_score),
                "similarity": float(sim_map.get(pid, 0.0)),
            })
        
        reranked.sort(key=lambda r: r["final_score"], reverse=True)
        
        # 8) top_k 개수만큼 반환
        if top_k == 1:
            return reranked[0] if reranked else None
        else:
            return reranked[:top_k]
            
    except Exception as e:
        print(f"❌ 상품 추천 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_recommendation(request_data: Any) -> Dict[str, Any]:
    """
    Get recommendation using Cross-Encoder based system.
    """
    user_id = request_data.user_id
    intention = getattr(request_data, 'intention', None)
    user_data = request_data.user_data
    target_brands = getattr(request_data, 'target_brand', None)
    
    print(f"\n🎯 추천 요청 수신:")
    print(f"  - User ID: {user_id}")
    print(f"  - Intention: {intention}")
    print(f"  - Target Brands: {target_brands}")
    
    # Cross-Encoder 기반 추천 시스템 호출
    recommendation = await recommend_product_with_brands(
        user_id=user_id,
        user_data=user_data,
        target_brands=target_brands if target_brands else [],
        top_k=1
    )
    
    if recommendation:
        print(f"  ✅ 상품 추천 성공: {recommendation['name']} (ID: {recommendation['product_id']})")
        print(f"  📊 Score: ce={recommendation['ce_score']:.4f}, kw_bonus={recommendation['kw_bonus']:.3f}, final={recommendation['final_score']:.4f}")
        
        result = {
            "product_id": recommendation['product_id'],
            "product_name": recommendation['name'],
            "score": recommendation['final_score'],
            "reason": f"Cross-Encoder 점수: {recommendation['ce_score']:.4f}, 키워드 매칭: {recommendation['kw_bonus']:.3f}",
            "product_data": {
                "product_id": recommendation['product_id'],
                "brand": recommendation['brand'],
                "name": recommendation['name'],
                "category": {
                    "major": recommendation['category_major'],
                    "middle": recommendation['category_middle'],
                    "small": recommendation['category_small'],
                },
                "price": {
                    "original_price": recommendation['price_final'],
                    "discounted_price": recommendation['price_final'],
                    "discount_rate": recommendation['discount_rate'],
                },
                "review": {
                    "score": recommendation['review_score'],
                    "count": recommendation['review_count'],
                    "top_keywords": [],
                },
                "description_short": f"{recommendation['name']} - {recommendation['brand']}",
            }
        }
        return result
    
    # 추천 실패 시 기본값 반환
    print("  ⚠️ 추천 실패, 기본값 반환")
    return {
        "product_id": "UNKNOWN",
        "product_name": "추천 실패",
        "score": 0.0,
        "reason": "상품 추천에 실패했습니다.",
    }


