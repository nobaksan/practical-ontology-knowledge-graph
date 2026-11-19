#!/usr/bin/env python3
"""
GraphRAG 서브그래프 패커 및 인터랙티브 AI 에이전트 CLI — 모의 구현
사용자 질문에서 온톨로지 엔티티를 매칭하고, 다중 홉 관계망(서브그래프)을 인출하여
출처가 명시된 팩트 기반 응답을 생성하는 흐름을 보여 준다.

주의: 이 스크립트는 Neo4j 에 접속하지 않고 LLM 도 호출하지 않는다. 질문과 무관하게
mock_graph_lookup() 의 고정 서브그래프를 패킹하고, 응답 문구도 고정 문자열을 출력한다.
진행률·점검일·제품 ID(PROD-EV01)·공장 ID(FAC-01) 같은 값은 생성 그래프에 없는 예시 값이다.
"""

import sys

def mock_graph_lookup(query):
    # 실제 환경에서는 Neo4j 드라이버(neo4j-python-driver) 세션을 통해 실행됨
    subgraph = {
        "seed_entity": "Customer(name='현대자동차', id='ERP_CUST_101')",
        "nodes": [
            {"id": "ERP_CUST_101", "type": "Customer", "name": "현대자동차(주)"},
            {"id": "ORD-2026-A", "type": "Order", "amount": "₩12.5억"},
            {"id": "PROD-EV01", "type": "Product", "name": "EV배터리팩 케이스"},
            {"id": "WO-9021", "type": "WorkOrder", "status": "IN_PROGRESS", "progress": "85%"},
            {"id": "CNC-04", "type": "Machine", "status": "OPERATIONAL", "next_maint": "2026-11-15"},
            {"id": "FAC-01", "type": "Factory", "name": "울산 1공장"}
        ],
        "edges": [
            "(ERP_CUST_101)-[:PLACED_ORDER]->(ORD-2026-A)",
            "(ORD-2026-A)-[:INCLUDES]->(PROD-EV01)",
            "(WO-9021)-[:REQUIRES]->(PROD-EV01)",
            "(WO-9021)-[:ASSIGNED_TO {valid_from: '2026-03-01', valid_to: null}]->(CNC-04)",
            "(CNC-04)-[:LOCATED_IN]->(FAC-01)"
        ]
    }
    return subgraph

def pack_subgraph_context(subgraph):
    lines = ["=== 지식그래프 인출 팩트 컨텍스트 (Verified Subgraph Facts) ==="]
    for edge in subgraph["edges"]:
        lines.append(f"FACT: {edge}")
    lines.append("\n=== 노드 상세 속성 원장 ===")
    for node in subgraph["nodes"]:
        lines.append(f"NODE[{node['id']}]: type={node['type']}, props={node}")
    return "\n".join(lines)

def run_agent(query):
    print(f"\n[CLI] 사용자 질문 수신: \"{query}\"")
    print("-" * 65)
    print("[1/4] 온톨로지 개체명 추출 (모의: 고정 값)... Customer('현대자동차'), Product('배터리팩')")
    print("[2/4] 4홉 서브그래프 인출 (모의: DB 접속 없이 고정 서브그래프 사용)...")
    
    subgraph = mock_graph_lookup(query)
    context = pack_subgraph_context(subgraph)
    tokens = len(context.split()) * 1.3
    
    print(f"[3/4] 서브그래프 패킹 완료: {len(subgraph['nodes'])}개 노드, {len(subgraph['edges'])}개 엣지 (약 {int(tokens)} 토큰)")
    print("[4/4] 응답 출력 (모의: LLM 호출 없이 고정 문구)...")
    print("-" * 65)
    print("【AI 에이전트 응답 — 모의 출력】")
    print(f"현대자동차(ERP_CUST_101)의 수주 건(ORD-2026-A, 12.5억 원)에 해당하는 EV배터리팩 생산은")
    print(f"현재 '울산 1공장' 3호 라인의 'CNC-04' 설비에 배정(WO-9021)되어 진행률 85%로 정상 가동 중입니다.")
    print(f"\n[운영 위험 감지 알림]")
    print(f"설비 CNC-04의 차기 정기점검일이 2026-11-15로 예정되어 있어 납기 지연 방지를 위해 사전 부하 분산을 권고합니다.")
    print(f"[검증 출처 노드: #WO-9021, #CNC-04, #ORD-2026-A]")
    print("-" * 65)

if __name__ == "__main__":
    q = "현대자동차의 배터리팩 수주와 관련된 현재 설비 가동 상태와 위험 요소를 알려줘"
    if len(sys.argv) > 1:
        q = " ".join(sys.argv[1:])
    run_agent(q)
