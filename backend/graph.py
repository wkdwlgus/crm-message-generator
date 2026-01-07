"""
LangGraph Workflow Definition
5개 노드를 연결한 메시지 생성 워크플로우
"""
from langgraph.graph import StateGraph, END
from actions.orchestrator import orchestrator_node, GraphState
from actions.info_retrieval import info_retrieval_node
from actions.message_writer import message_writer_node
from actions.compliance_check import compliance_check_node
from actions.save_crm import save_crm_message_node
from actions.retrieve_crm import retrieve_crm_node
from actions.personalize import personalize_message_node
from actions.return_response import return_response_node
from config import settings


def should_retry(state: GraphState) -> str:
    """
    재시도 여부 결정
    """
    compliance_passed = state.get("compliance_passed", False)
    retry_count = state.get("retry_count", 0)
    max_retries = settings.max_retry_count
    
    if compliance_passed:
        # Compliance 통과 → save_crm으로 이동
        return "save_crm"
    elif retry_count < max_retries:
        # 재시도 가능 → message_writer로 이동
        return "message_writer"
    else:
        # 최대 재시도 횟수 초과 → return_response로 이동 (에러 응답)
        return "return_response"


def check_cache(state: GraphState) -> str:
    """
    CRM Cache Hit 여부에 따른 경로 분기
    """
    if state.get("cache_hit", False):
        return "personalize"
    else:
        return "message_writer"


def create_workflow() -> StateGraph:
    """
    LangGraph 워크플로우 생성
    
    Returns:
        컴파일된 StateGraph
    """
    # StateGraph 생성
    workflow = StateGraph(GraphState)
    
    # 노드 추가
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("info_retrieval", info_retrieval_node)
    workflow.add_node("retrieve_crm", retrieve_crm_node)
    workflow.add_node("message_writer", message_writer_node)
    workflow.add_node("compliance_check", compliance_check_node)
    workflow.add_node("save_crm", save_crm_message_node)
    workflow.add_node("personalize", personalize_message_node)
    workflow.add_node("return_response", return_response_node)
    
    # 엣지 설정
    workflow.set_entry_point("orchestrator")
    workflow.add_edge("orchestrator", "info_retrieval")
    workflow.add_edge("info_retrieval", "retrieve_crm")
    
    # 조건부 엣지: retrieve_crm → personalize (Hit) or message_writer (Miss)
    workflow.add_conditional_edges(
        "retrieve_crm",
        check_cache,
        {
            "personalize": "personalize",
            "message_writer": "message_writer"
        }
    )
    
    workflow.add_edge("message_writer", "compliance_check")
    
    # 조건부 엣지: compliance_check → save_crm (Pass) or message_writer (Retry)
    workflow.add_conditional_edges(
        "compliance_check",
        should_retry,
        {
            "message_writer": "message_writer",
            "save_crm": "save_crm",
            "return_response": "return_response",
        }
    )
    
    workflow.add_edge("save_crm", "personalize")
    workflow.add_edge("personalize", "return_response")
    workflow.add_edge("return_response", END)
    
    # 워크플로우 컴파일
    app = workflow.compile()
    
    return app


# 전역 워크플로우 인스턴스
message_workflow = create_workflow()
