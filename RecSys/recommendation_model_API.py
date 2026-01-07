import os
import json
from typing import Dict, Any, List, Optional, Tuple
from openai import OpenAI
import httpx
from config import (
    settings,
    # Cross-Encoder 설정
    TOP_K, CANDIDATE_POOL, EMBED_MODEL, EMBED_DIM, CE_MODEL, KW_BONUS_ALPHA,
    CUSTOMER_ID_COL, PRODUCT_VECTOR_FK_COL,
    # 동의어 매핑
    SKIN_TYPE_MAP, CONCERN_MAP, TONE_MAP,
    # 키워드 번역
    KEYWORD_TRANSLATION,
    # 날씨 키워드
    WEATHER_KEYWORDS, WEATHER_PRIORITY_KEYWORDS
)
from sentence_transformers import CrossEncoder
import torch
from datetime import datetime

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
    
    # preferred_tone이 리스트일 수 있음 (DB 스키마 차이)
    tone = customer.get("preferred_tone")
    if isinstance(tone, list):
        tone = tone[0] if tone else None
    
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


def expand_keywords(keywords: List[str]) -> List[str]:
    """영어 키워드를 한글 동의어로 확장하여 매칭률 향상"""
    expanded = []
    for kw in keywords:
        # 원본 키워드 추가
        expanded.append(kw)
        
        # 정규화: 소문자 변환, 언더스코어 제거
        normalized = kw.lower().replace("_", "").replace("-", "").replace(" ", "")
        
        # 매핑된 한글 동의어 추가
        if normalized in KEYWORD_TRANSLATION:
            expanded.extend(KEYWORD_TRANSLATION[normalized])
    
    return expanded


def get_current_season() -> str:
    """현재 날짜를 기준으로 시즌 반환"""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    elif month in [9, 10, 11]:
        return "fall"
    else:  # 12, 1, 2
        return "winter"


def keyword_bonus(
    user_keywords: List[str], 
    product_content: str, 
    product_keywords: List[str], 
    skin_concerns: List[str] = None,
    weather_keywords: List[str] = None,
    current_season: str = None
) -> Tuple[float, Dict[str, Any]]:
    """키워드 매칭 보너스 계산 (0~1) - 단순 카운트 방식 + 날씨 우선순위 가중치
    
    유저의 키워드 + 피부고민이 제품 본문 + 제품 키워드에서 몇 번 나오는지 카운트
    
    Args:
        user_keywords: 유저의 키워드 리스트 (확장된 것)
        product_content: 제품 본문 (products_vector.content)
        product_keywords: 제품 키워드 리스트 (products.keywords)
        skin_concerns: 유저의 피부고민 (추가 검색 키워드)
        weather_keywords: 날씨/시즌 관련 키워드 (intent=weather일 때)
        current_season: 현재 계절 (spring/summer/fall/winter)
    
    Returns:
        (score, details): 0~1 점수와 상세 정보
    """
    # 검색할 키워드 수집
    kws = [k.strip() for k in (user_keywords or []) if k and str(k).strip()]
    
    # 피부고민 추가
    if skin_concerns:
        kws.extend([k.strip() for k in skin_concerns if k and str(k).strip()])
    
    # weather intent일 경우 weather_keywords 추가
    if weather_keywords:
        kws.extend([k.strip() for k in weather_keywords if k and str(k).strip()])
    
    if not kws:
        return 0.0, {"matched_keywords": [], "hit_count": 0, "total_keywords": 0, "priority_hits": 0}

    # 검색 대상: 제품 본문 + 제품 키워드 합치기
    search_text = (product_content or "").lower()
    if product_keywords:
        search_text += " " + " ".join([str(k).lower() for k in product_keywords])
    
    # 띄어쓰기 제거한 정규화 버전
    search_text_normalized = search_text.replace(" ", "")

    # 계절별 우선순위 키워드 가져오기
    priority_kws = []
    if current_season and current_season in WEATHER_PRIORITY_KEYWORDS:
        priority_kws = [k.lower() for k in WEATHER_PRIORITY_KEYWORDS[current_season]]

    # 키워드 매칭 카운트 (우선순위 키워드는 2배 가중치)
    hit_count = 0.0
    matched_keywords = []
    priority_matched = []
    
    for kw in kws:
        k = kw.lower()
        k_normalized = k.replace(" ", "")
        
        # 원본 매칭 OR 정규화 매칭
        if (k in search_text) or (k_normalized in search_text_normalized):
            matched_keywords.append(kw)
            
            # 우선순위 키워드인지 확인 (계절별 핵심 키워드)
            is_priority = any(pk in k or k in pk for pk in priority_kws)
            
            if is_priority:
                hit_count += 2.0  # 우선순위 키워드는 2배 가중치
                priority_matched.append(kw)
            else:
                hit_count += 1.0  # 일반 키워드

    # 0~1 정규화 (우선순위 키워드가 있을 수 있으므로 최대값 조정)
    # 모든 키워드가 우선순위라면 max = len(kws) * 2
    max_possible_score = len(kws) * 2.0 if priority_kws else len(kws)
    score = hit_count / max(max_possible_score, 1)
    
    details = {
        "matched_keywords": matched_keywords,
        "hit_count": int(hit_count),  # 실제 가중치 적용된 값
        "total_keywords": len(kws),
        "priority_hits": len(priority_matched)  # 우선순위 키워드 매칭 수
    }
    
    return float(min(1.0, max(0.0, score))), details


async def fetch_products_from_supabase() -> Dict[str, str]:
    """
    Fetch products from Supabase and format them for the LLM.
    (Deprecated - 이제 recommend_product_with_brands 사용)
    """
    return {}

    # url = f"{settings.SUPABASE_URL}/rest/v1/products"
    # headers = {
    #     "apikey": settings.SUPABASE_KEY,
    #     "Authorization": f"Bearer {settings.SUPABASE_KEY}",
    # }

    # try:
    #     async with httpx.AsyncClient() as http_client:
    #         response = await http_client.get(url, headers=headers)
    #         response.raise_for_status()
    #         products_data = response.json()
            
    #         # Format: "ID": "Name (Brand, Category, Description)"
    #         formatted_products = {}
    #         full_data = {}  # Store full product data
    #         for p in products_data:
    #             # Adjust field names based on actual DB schema
    #             # Schema: id, product_code, brand, name, category_major, category_middle, category_small, 
    #             # price_original, price_final, discount_rate, review_score, review_count, features, analytics, keywords
                
    #             p_id = p.get("product_code") or str(p.get("id"))
    #             name = p.get("name")
    #             brand = p.get("brand", "")
                
    #             # Construct category string
    #             cats = [p.get("category_major"), p.get("category_middle"), p.get("category_small")]
    #             category = " > ".join([c for c in cats if c])
                
    #             # Construct description from keywords and features
    #             keywords = p.get("keywords", "")
    #             price = p.get("price_final")
    #             review_score = p.get("review_score")
                
    #             desc_parts = []
    #             if keywords:
    #                 desc_parts.append(f"Keywords: {keywords}")
    #             if price:
    #                 desc_parts.append(f"Price: {price}")
    #             if review_score:
    #                 desc_parts.append(f"Rating: {review_score}")
                
    #             desc = ", ".join(desc_parts)
                
    #             if p_id and name:
    #                 info = f"{name} (Brand: {brand}, Category: {category}, {desc})"
    #                 formatted_products[p_id] = info
    #                 # Store full product data
    #                 full_data[p_id] = p
            
    #         PRODUCTS_CACHE = formatted_products
    #         PRODUCTS_FULL_DATA = full_data
            
    #         # Debug: Print first 3 products to verify format
    #         print("DEBUG: Sample products from DB:")
    #         for i, (pid, info) in enumerate(formatted_products.items()):
    #             if i >= 3: break
    #             print(f" - {pid}: {info}")
                
    #         return formatted_products
            
    # except Exception as e:
    #     print(f"Failed to fetch products from Supabase: {e}")
    #     # Fallback to empty dict or hardcoded list if needed
    #     return {}

async def recommend_product_with_brands(
    user_id: str,
    user_data: Any,
    target_brands: List[str] = None,
    top_k: int = 1,
    intent: str = ""
) -> Optional[Dict[str, Any]]:
    """
    유저 ID와 브랜드 리스트를 받아 Cross-Encoder 기반으로 최고의 상품을 추천합니다.
    
    Args:
        user_id: 사용자 ID
        user_data: CustomerProfile 객체 (user_data에서 추출한 정보)
        target_brands: 추천할 브랜드 리스트 (None이면 모든 브랜드)
        top_k: 반환할 상품 개수 (기본값: 1)
        intent: 추천 의도 ("": regular, "event": 할인율 높은 제품, "weather": 날씨별 제품)
        
    Returns:
        추천 상품 정보 dict 또는 None
    """
    try:
        # Supabase 및 OpenAI 클라이언트 초기화
        from supabase import create_client, Client
        sb: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
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

        print(f"customer_resp: {customer_resp}")

        
        if not customer_resp.data:
            print(f"[WARN] customers에서 {CUSTOMER_ID_COL}={user_id}를 찾지 못함")
            return None
        
        customer = customer_resp.data[0]
        user_keywords_raw = normalize_list(customer.get("keywords"))
        
        # 키워드 확장: 영어 -> 한글 동의어 추가
        user_keywords = expand_keywords(user_keywords_raw)
        print(f"  🔍 키워드 확장: {user_keywords_raw} → {len(user_keywords)}개")
        
        # [Fix] 피부 고민 정의 (키워드 보너스 계산용)
        concerns = with_kr(normalize_list(customer.get("skin_concerns")), CONCERN_MAP)

        # intent 처리: weather일 경우 시즌별 키워드 추가
        weather_keywords = []
        if intent == "weather":
            current_season = get_current_season()
            weather_keywords = WEATHER_KEYWORDS.get(current_season, [])
            print(f"  🌡️ Weather Intent: {current_season} season - 키워드: {weather_keywords[:3]}...")
        
        # 2) 쿼리 텍스트 생성
        query_text = build_user_query_text(customer)
        
        # 3) 임베딩 생성
        query_emb = embed_text(oa, query_text)
        
        # 4) 벡터 유사도 검색 (후보 풀) - 브랜드 필터링 적용
        if target_brands and len(target_brands) > 0:
            # 브랜드가 지정된 경우
            print(f"\n🔍 [RPC Search] 브랜드 지정 검색: {target_brands}")
            
            rpc_payload = {
                "query_embedding": query_emb,
                "match_count": CANDIDATE_POOL,
                "filter_brands": target_brands
            }
            
            try:
                response = sb.rpc('match_products', rpc_payload).execute()
                matches = response.data or []
                
                print(f"📊 [RPC Response] 브랜드 필터링 검색 결과: {len(matches)}개")
                
                # 결과 출력 (상위 3개)
                if matches:
                    print(f"  - 상위 3개 샘플:")
                    for i, item in enumerate(matches[:3], 1):
                        print(f"    {i}. ID: {item.get('product_id')}, 유사도: {item.get('similarity', 0):.4f}")
                
            except Exception as e:
                print(f"❌ [RPC Error] 브랜드 필터링 검색 실패: {e}")
                matches = []
        else:
            # 브랜드 지정 없음 - 일반 검색
            print(f"\n🔍 [RPC Search] 브랜드 미지정 - 전체 검색 (pool={CANDIDATE_POOL})")
            
            rpc_payload = {
                "filter": {},
                "match_count": CANDIDATE_POOL,
                "query_embedding": query_emb,
            }
            
            match_resp = sb.rpc("match_products", rpc_payload).execute()
            matches = match_resp.data or []
            
            print(f"📊 [RPC Response] 유사도 검색 결과: {len(matches)}개")
        
        if not matches:
            print("❌ [ERROR] 최종 유사도 검색 결과가 없습니다.")
            return None
        
        matches.sort(key=lambda m: float(m.get("similarity", 0.0)), reverse=True)
        candidate_ids = [m["product_id"] for m in matches]
        sim_map = {m["product_id"]: float(m["similarity"]) for m in matches}
        
        print(f"\n📋 [Candidate Pool] 최종 후보:")
        print(f"  - 후보 ID 수: {len(candidate_ids)}개")
        print(f"  - 상위 5개 ID: {candidate_ids[:5]}")
        
        # 5) products 상세 정보 조회
        # RPC에서 이미 브랜드 필터링이 적용되었으므로 추가 필터 불필요
        print(f"\n🗃️ [Products Table] 상세 정보 조회:")
        products_resp = (
            sb.table("products")
            .select("id, brand, name, category_major, category_middle, category_small, price_final, discount_rate, review_score, review_count")
            .in_("id", candidate_ids)
            .execute()
        )
        products = products_resp.data or []
        
        print(f"\n📦 [Products Result] 조회 결과:")
        print(f"  - 조회된 제품 수: {len(products)}개")
        if products:
            print(f"  - 브랜드 분포: {dict((b, sum(1 for p in products if p.get('brand') == b)) for b in set(p.get('brand') for p in products))}")
            print(f"  - 상위 3개:")
            for i, p in enumerate(products[:3], 1):
                print(f"    {i}. [{p.get('brand')}] {p.get('name')[:30]}... (ID={p.get('id')})")
        
        if not products:
            print(f"\n❌ [ERROR] products 테이블 조회 실패")
            if target_brands:
                print(f"  → 브랜드 필터({target_brands}) 때문에 제품이 없을 수 있음")
                print(f"  → candidate_ids에는 {len(candidate_ids)}개가 있었지만 해당 브랜드 제품이 없음")
            else:
                print(f"  → candidate_ids={candidate_ids[:5]}... 중 products 테이블에 없는 ID들")
            return None
        
        prod_map = {p["id"]: p for p in products}
        filtered_ids = list(prod_map.keys())
        
        print(f"\n✅ [Products Filtered] 최종 제품 풀:")
        print(f"  - 필터링 후 제품 수: {len(filtered_ids)}개")
        
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
            p = prod_map.get(pid)
            
            # 제품 키워드 가져오기
            product_keywords = normalize_list(p.get("keywords"))
            
            # 키워드 보너스 계산 (피부고민 + 날씨 우선순위 키워드 포함)
            kwb, kw_details = keyword_bonus(
                user_keywords=user_keywords,
                product_content=content,
                product_keywords=product_keywords,
                skin_concerns=concerns,
                weather_keywords=weather_keywords if intent == "weather" else None,
                current_season=current_season if intent == "weather" else None
            )
            
            final_score = float(ce_score) + KW_BONUS_ALPHA * kwb
            
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
        
        # intent에 따른 정렬
        if intent == "event":
            # Event Intent: final_score로 Top 5 추출 후, Top 5 중 할인율 우선
            reranked.sort(key=lambda r: r["final_score"], reverse=True)
            if len(reranked) >= 5:
                top_5 = reranked[:5]
                top_5.sort(key=lambda r: (r.get("discount_rate") or 0), reverse=True)
                reranked = top_5 + reranked[5:]
            print(f"  🎁 Event Intent: Top 5 중 할인율 우선 (1위 할인율: {reranked[0].get('discount_rate', 0)}%)")
        else:
            # regular 또는 weather: final_score로 정렬
            reranked.sort(key=lambda r: r["final_score"], reverse=True)
        
        # 9) 디버그 출력 (상위 3개)
        if reranked:
            print(f"\n🏆 [Final Ranking] Top 3 추천 결과:")
            for i, r in enumerate(reranked[:3], 1):
                print(f"  {i}. [{r.get('brand')}] {r['name'][:30]}...")
                print(f"     - CE: {r['ce_score']:.4f}, KW: {r['kw_bonus']:.3f}, Final: {r['final_score']:.4f}")
                print(f"     - 할인: {r.get('discount_rate', 0)}%, 리뷰: {r.get('review_score', 0)}⭐")
            
            # 최종 1위 제품 상세 정보
            winner = reranked[0]
            print(f"\n🎯 [Winner] 최종 선택:")
            print(f"  - Brand: {winner.get('brand')} ← {'✅ 존재' if winner.get('brand') else '❌ 누락'}")
            print(f"  - Name: {winner.get('name')}")
            print(f"  - Product ID: {winner.get('product_id')}")
        
        # 8) top_k 개수만큼 반환
        if top_k == 1:
            result = reranked[0] if reranked else None
            if result:
                # 반환 전 brand 필드 재확인
                if not result.get('brand'):
                    print(f"\n⚠️ [CRITICAL] 반환할 제품에 brand가 없음! prod_map 확인:")
                    pid = result.get('product_id')
                    if pid and int(pid) in prod_map:
                        print(f"  - prod_map[{pid}]: {prod_map[int(pid)]}")
            return result
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
    intention = getattr(request_data, 'intention', None) or ""
    user_data = request_data.user_data
    target_brands = getattr(request_data, 'target_brand', None)

    print(f"user_data: {user_data}, target_brands: {target_brands}")
    
    print(f"\n🎯 추천 요청 수신:")
    print(f"  - User ID: {user_id}")
    print(f"  - Intention: {intention}")
    print(f"  - Target Brands: {target_brands}")
    
    # Cross-Encoder 기반 추천 시스템 호출
    recommendation = await recommend_product_with_brands(
        user_id=user_id,
        user_data=user_data,
        target_brands=target_brands if target_brands else [],
        top_k=1,
        intent=intention
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


