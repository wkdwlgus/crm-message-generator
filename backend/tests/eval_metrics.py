"""
Evaluation harness for Blooming metrics.

Metrics covered:
1) RecSys diversity / intent differentiation
2) Message quality via LLM-as-a-judge
3) Workflow stability / recovery (manual flow with stubs)
4) Cost per generation (token-based estimate)
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx
import sys
from pathlib import Path

# Ensure backend/ is on sys.path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))


@dataclass
class EvalConfig:
    backend_base_url: str
    recsys_base_url: str
    user_ids: List[str]
    channels: List[str]
    intents: List[str]
    samples_per_user: int
    openai_api_key: Optional[str]
    openai_model: str
    enable_llm_judge: bool
    input_cost_per_1k: float
    output_cost_per_1k: float


def _safe_mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.mean(values))


def _safe_median(values: List[float]) -> float:
    if not values:
        return 0.0
    return float(statistics.median(values))


def _post_json(url: str, payload: Dict[str, Any], timeout_s: int = 60) -> Dict[str, Any]:
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        return resp.json()


def _get_json(url: str, headers: Dict[str, str], params: Dict[str, Any], timeout_s: int = 60) -> Dict[str, Any]:
    with httpx.Client(timeout=timeout_s) as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        return resp.json()


def evaluate_recsys_diversity(cfg: EvalConfig) -> Dict[str, Any]:
    intent_pairs = [
        ("", "event"),
        ("", "weather"),
        ("event", "weather"),
    ]
    per_user = []
    for user_id in cfg.user_ids:
        products_by_intent: Dict[str, Dict[str, Any]] = {}
        for intent in cfg.intents:
            payload = {
                "user_id": user_id,
                "intention": intent,
            }
            try:
                result = _post_json(
                    f"{cfg.recsys_base_url}/recommend",
                    payload,
                    timeout_s=120,
                )
            except Exception as exc:
                products_by_intent[intent] = {"error": str(exc)}
                continue

            product_data = result.get("product_data") or {}
            products_by_intent[intent] = {
                "product_id": result.get("product_id"),
                "brand": product_data.get("brand"),
                "name": product_data.get("name"),
            }

        product_ids = [
            p.get("product_id")
            for p in products_by_intent.values()
            if p.get("product_id")
        ]
        unique_products = len(set(product_ids))
        intent_diversity = unique_products / max(1, len(cfg.intents))

        pairwise_overlap = []
        for a, b in intent_pairs:
            pa = products_by_intent.get(a, {}).get("product_id")
            pb = products_by_intent.get(b, {}).get("product_id")
            if pa and pb:
                pairwise_overlap.append(1.0 if pa == pb else 0.0)

        per_user.append(
            {
                "user_id": user_id,
                "intent_diversity": intent_diversity,
                "pairwise_overlap": _safe_mean(pairwise_overlap),
                "products_by_intent": products_by_intent,
            }
        )

    return {
        "avg_intent_diversity": _safe_mean([u["intent_diversity"] for u in per_user]),
        "avg_pairwise_overlap": _safe_mean([u["pairwise_overlap"] for u in per_user]),
        "per_user": per_user,
    }


def _judge_message_quality(
    api_key: str,
    model: str,
    message: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    prompt = f"""
You are a strict CRM message evaluator.
Score the message on 1-5 (5=best) for:
- personalization
- brand_tone
- clarity
- cta_strength
- compliance_risk (higher score means lower risk)
Return JSON only.

Context:
{json.dumps(context, ensure_ascii=True)}

Message:
{message}

Return JSON:
{{
  "personalization": 1-5,
  "brand_tone": 1-5,
  "clarity": 1-5,
  "cta_strength": 1-5,
  "compliance_risk": 1-5,
  "overall": 1-5,
  "notes": "short text"
}}
"""
    result = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        response_format={"type": "json_object"},
    )
    content = result.choices[0].message.content or "{}"
    return json.loads(content)


def evaluate_message_quality(cfg: EvalConfig) -> Dict[str, Any]:
    if not cfg.enable_llm_judge or not cfg.openai_api_key:
        return {"skipped": True, "reason": "LLM judge disabled or missing API key"}

    scores = []
    for user_id in cfg.user_ids:
        for channel in cfg.channels:
            headers = {"x-user-id": user_id}
            params = {
                "channel": channel,
                "reason": "regular",
                "persona": "P1",
            }
            try:
                response = _get_json(
                    f"{cfg.backend_base_url}/message",
                    headers=headers,
                    params=params,
                    timeout_s=120,
                )
            except Exception as exc:
                scores.append({"error": str(exc), "user_id": user_id, "channel": channel})
                continue

            message = response.get("message") or response.get("content") or ""
            if not message:
                scores.append({"error": "empty_message", "user_id": user_id, "channel": channel})
                continue

            context = {
                "user_id": user_id,
                "channel": channel,
                "reason": "regular",
            }
            judge = _judge_message_quality(cfg.openai_api_key, cfg.openai_model, message, context)
            judge["user_id"] = user_id
            judge["channel"] = channel
            scores.append(judge)

    numeric_fields = [
        "personalization",
        "brand_tone",
        "clarity",
        "cta_strength",
        "compliance_risk",
        "overall",
    ]
    aggregates = {}
    for field in numeric_fields:
        values = [s[field] for s in scores if isinstance(s.get(field), (int, float))]
        aggregates[f"avg_{field}"] = _safe_mean(values)

    aggregates["raw"] = scores
    return aggregates


def _build_sample_state() -> Dict[str, Any]:
    from models.user import CustomerProfile

    user = CustomerProfile(
        user_id="eval_user",
        name="00",
        age_group="30s",
        membership_level="VIP",
        skin_type=["Dry"],
        skin_concerns=["Wrinkle"],
        preferred_tone="Warm_Spring",
        keywords=["Moisture"],
    )
    return {
        "user_id": "eval_user",
        "user_data": user,
        "recommended_product_id": "",
        "product_data": {
            "product_id": "",
            "brand": "Innisfree",
            "name": "Moisture Cream",
            "category": {"major": "Skincare", "middle": "Cream", "small": "Moisture"},
            "price": {"original_price": 30, "discounted_price": 25, "discount_rate": 15},
            "review": {"score": 4.5, "count": 120, "top_keywords": ["hydrating"]},
            "description_short": "Hydrating daily cream",
        },
        "brand_tone": {"brand_name": "Innisfree", "tone_manner_style": "Friendly", "tone_manner_examples": []},
        "channel": "SMS",
        "message": "",
        "message_template": "",
        "compliance_passed": False,
        "retry_count": 0,
        "error": "",
        "error_reason": "",
        "success": False,
        "retrieved_legal_rules": [
            {
                "id": "mock_rule_1",
                "rule_title": "No medical claims",
                "severity": "HIGH",
                "rule_description": "No disease treatment claims",
                "prohibited_examples": ["treat acne"],
                "allowed_examples": ["skin care"],
                "regulation_categories": {"legal_basis": "Cosmetics Act", "category_name": "Medical"},
            }
        ],
        "crm_reason": "regular",
        "weather_detail": "",
        "target_brand": "",
        "target_persona": "1",
        "recommended_brand": "Innisfree",
    }


def evaluate_workflow_stability_and_recovery(cfg: EvalConfig) -> Dict[str, Any]:
    from actions import compliance_check
    from actions.message_writer import message_writer_node

    original_judge = compliance_check.call_llm_judge
    from services.llm_client import llm_client

    original_generate = llm_client.generate_chat_completion
    calls = {"judge": 0}

    def stub_generate_chat_completion(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        return {
            "content": "Hello {{customer_name}}, check out our offer.",
            "usage": {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
        }

    def sequence_judge(_prompt: str) -> Dict[str, Any]:
        calls["judge"] += 1
        if calls["judge"] <= 2:
            return {
                "passed": False,
                "violated_rules": [
                    {
                        "rule_id": "mock_rule_1",
                        "rule_title": "No medical claims",
                        "violated_expression": "treat acne",
                        "reason": "medical claim",
                        "severity": "HIGH",
                    }
                ],
                "reasoning": "medical claim detected",
                "confidence": 0.9,
                "suggestions": "remove medical claim",
            }
        return {
            "passed": True,
            "violated_rules": [],
            "reasoning": "clean",
            "confidence": 0.9,
            "suggestions": "",
        }

    llm_client.generate_chat_completion = stub_generate_chat_completion
    compliance_check.call_llm_judge = sequence_judge

    state = _build_sample_state()
    attempts = 0
    max_retries = 5
    while True:
        attempts += 1
        state = message_writer_node(state)
        state = compliance_check.compliance_check_node(state)
        if state.get("compliance_passed"):
            break
        if state.get("retry_count", 0) >= max_retries:
            break

    compliance_check.call_llm_judge = original_judge
    llm_client.generate_chat_completion = original_generate

    return {
        "attempts": attempts,
        "final_passed": state.get("compliance_passed", False),
        "retry_count": state.get("retry_count", 0),
        "error_reason_present": bool(state.get("error_reason")),
    }


def estimate_generation_cost(cfg: EvalConfig) -> Dict[str, Any]:
    from actions.message_writer import message_writer_node
    from services.llm_client import llm_client

    usage_records = []
    original_generate = llm_client.generate_chat_completion

    def wrapped_generate(*args: Any, **kwargs: Any) -> Dict[str, Any]:
        result = original_generate(*args, **kwargs)
        usage_records.append(result.get("usage", {}))
        return result

    def stub_generate(*_args: Any, **_kwargs: Any) -> Dict[str, Any]:
        usage = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
        usage_records.append(usage)
        return {"content": "Hello {{customer_name}}", "usage": usage}

    if cfg.enable_llm_judge and cfg.openai_api_key:
        llm_client.generate_chat_completion = wrapped_generate
    else:
        llm_client.generate_chat_completion = stub_generate

    for _ in range(cfg.samples_per_user):
        state = _build_sample_state()
        message_writer_node(state)

    llm_client.generate_chat_completion = original_generate

    prompt_tokens = [u.get("prompt_tokens", 0) for u in usage_records if u]
    completion_tokens = [u.get("completion_tokens", 0) for u in usage_records if u]

    avg_prompt = _safe_mean(prompt_tokens)
    avg_completion = _safe_mean(completion_tokens)
    avg_cost = (avg_prompt / 1000.0) * cfg.input_cost_per_1k + (avg_completion / 1000.0) * cfg.output_cost_per_1k

    return {
        "samples": len(usage_records),
        "avg_prompt_tokens": avg_prompt,
        "avg_completion_tokens": avg_completion,
        "estimated_cost_per_message": avg_cost,
        "pricing_per_1k": {
            "input": cfg.input_cost_per_1k,
            "output": cfg.output_cost_per_1k,
        },
    }


def _parse_args() -> EvalConfig:
    parser = argparse.ArgumentParser(description="Blooming evaluation harness")
    parser.add_argument("--backend", default=os.getenv("BACKEND_BASE_URL", "http://localhost:8000"))
    parser.add_argument("--recsys", default=os.getenv("RECSYS_BASE_URL", "http://localhost:8001"))
    parser.add_argument("--users", default=os.getenv("EVAL_USER_IDS", "user_12345,user_67890"))
    parser.add_argument("--channels", default=os.getenv("EVAL_CHANNELS", "SMS,KAKAO"))
    parser.add_argument("--intents", default=os.getenv("EVAL_INTENTS", ",event,weather"))
    parser.add_argument("--samples", type=int, default=int(os.getenv("EVAL_SAMPLES", "3")))
    parser.add_argument("--enable-llm", action="store_true")
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    parser.add_argument("--input-cost-per-1k", type=float, default=float(os.getenv("EVAL_INPUT_COST_PER_1K", "0.03")))
    parser.add_argument("--output-cost-per-1k", type=float, default=float(os.getenv("EVAL_OUTPUT_COST_PER_1K", "0.06")))

    args = parser.parse_args()
    user_ids = [u.strip() for u in args.users.split(",") if u.strip()]
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]
    intents = [i for i in [x.strip() for x in args.intents.split(",")] if i or i == ""]

    return EvalConfig(
        backend_base_url=args.backend,
        recsys_base_url=args.recsys,
        user_ids=user_ids,
        channels=channels,
        intents=intents,
        samples_per_user=args.samples,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        openai_model=args.openai_model,
        enable_llm_judge=args.enable_llm,
        input_cost_per_1k=args.input_cost_per_1k,
        output_cost_per_1k=args.output_cost_per_1k,
    )


def main() -> None:
    cfg = _parse_args()
    results = {
        "recsys_diversity": evaluate_recsys_diversity(cfg),
        "message_quality": evaluate_message_quality(cfg),
        "workflow_stability_recovery": evaluate_workflow_stability_and_recovery(cfg),
        "generation_cost": estimate_generation_cost(cfg),
        "meta": {
            "backend_base_url": cfg.backend_base_url,
            "recsys_base_url": cfg.recsys_base_url,
            "user_ids": cfg.user_ids,
            "channels": cfg.channels,
            "intents": cfg.intents,
            "samples_per_user": cfg.samples_per_user,
            "enable_llm_judge": cfg.enable_llm_judge,
        },
    }
    print(json.dumps(results, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
