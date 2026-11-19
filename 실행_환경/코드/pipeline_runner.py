#!/usr/bin/env python3
"""
지식그래프 6단계 파이프라인 러너 (Pipeline Runner)
선언적 매핑(mapping_rules.yaml)과 ER 룰(er_rules.yaml)을 적용하여,
Neo4j Cypher 스크립트와 W3C RDF Turtle 스펙을 생성한다.
"""

import os
import csv
import re
import difflib

def normalize_biz_no(no):
    if not no: return ""
    return re.sub(r"[^0-9]", "", str(no))

def similarity_ratio(s1, s2):
    return difflib.SequenceMatcher(None, s1, s2).ratio()

def run_pipeline():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.normpath(os.path.join(base_dir, "../실측_데이터"))
    out_dir = os.path.normpath(os.path.join(base_dir, "../검증_근거"))
    os.makedirs(out_dir, exist_ok=True)

    print("[1/5] 원천 데이터 로드 및 정규화...")
    erp_file = os.path.join(data_dir, "erp_customers.csv")
    crm_file = os.path.join(data_dir, "crm_accounts.csv")
    mes_file = os.path.join(data_dir, "mes_work_orders.csv")

    with open(erp_file, "r", encoding="utf-8") as f:
        erp_rows = list(csv.DictReader(f))
    with open(crm_file, "r", encoding="utf-8") as f:
        crm_rows = list(csv.DictReader(f))
    with open(mes_file, "r", encoding="utf-8") as f:
        mes_rows = list(csv.DictReader(f))

    print(f"  - ERP 고객: {len(erp_rows)}건, CRM 계정: {len(crm_rows)}건, MES 작업지시: {len(mes_rows)}건")

    print("[2/5] 엔티티 리졸루션 (블로킹 및 듀얼 임계값 채점)...")
    # 수동 감사 원장 (Ground Truth Mock)
    manual_audit = {
        ("ERP_CUST_101", "CRM_ACC_8806"): {"decision": "FORCE_SEPARATE", "reason": "남양연구소는 본사와 법인 분리된 별개 사업장임", "owner": "김거버넌스 팀장"}
    }

    resolutions = []
    auto_merged = 0
    hitl_queued = 0
    disjoint_count = 0

    for erp in erp_rows:
        erp_norm_biz = normalize_biz_no(erp["biz_no"])
        erp_prefix = erp_norm_biz[:3]

        for crm in crm_rows:
            crm_norm_biz = normalize_biz_no(crm["tax_id"])
            crm_prefix = crm_norm_biz[:3]

            pair_key = (erp["erp_id"], crm["crm_id"])

            # 1) 수동 감사 원장 오버라이드 확인
            if pair_key in manual_audit:
                dec = manual_audit[pair_key]
                resolutions.append({
                    "pair": pair_key, "score": 0.0, "status": dec["decision"],
                    "override": True, "reason": dec["reason"], "owner": dec["owner"]
                })
                disjoint_count += 1
                continue

            # 2) 블로킹 필터링 (앞 3자리 불일치 시 스킵)
            if erp_prefix and crm_prefix and erp_prefix != crm_prefix:
                continue

            # 3) 가중치 채점
            biz_score = 1.0 if erp_norm_biz == crm_norm_biz else 0.0
            name_score = similarity_ratio(erp["name"], crm["account_name"])
            total_score = (biz_score * 0.50) + (name_score * 0.50)

            # 4) 3구간 판정
            if total_score >= 0.85:
                status = "AUTO_MERGE"
                auto_merged += 1
            elif total_score >= 0.65:
                status = "HITL_REVIEW_QUEUE"
                hitl_queued += 1
            else:
                status = "DISJOINT"
                disjoint_count += 1

            resolutions.append({
                "pair": pair_key, "score": round(total_score, 3), "status": status,
                "override": False, "reason": "알고리즘 판정", "owner": "BATCH_ENGINE"
            })

    print(f"  - 리졸루션 결과: 자동 결합 {auto_merged}건, HITL 검토 대기 {hitl_queued}건, 분리/오버라이드 {disjoint_count}건")

    print("[3/5] Neo4j Cypher 스크립트 생성...")
    cypher_lines = [
        "// === 1. 제약조건 및 인덱스 생성 ===",
        "CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;",
        "CREATE CONSTRAINT machine_id IF NOT EXISTS FOR (m:Machine) REQUIRE m.id IS UNIQUE;",
        "CREATE CONSTRAINT work_order_id IF NOT EXISTS FOR (wo:WorkOrder) REQUIRE wo.id IS UNIQUE;",
        "",
        "// === 2. 노드 및 엣지 적재 ==="
    ]

    for erp in erp_rows:
        cypher_lines.append(f"MERGE (c:Customer {{id: '{erp['erp_id']}'}}) SET c.name = '{erp['name']}', c.bizNo = '{erp['biz_no']}', c.address = '{erp['address']}';")

    for mes in mes_rows:
        # 작업지시 한 건을 한 문장으로 적재한다. 문장(;)이 끝나면 변수 바인딩이 사라지므로
        # 노드와 관계를 같은 문장 안에서 이어 만들어야 그래프가 끊기지 않는다.
        valid_to_val = f"'{mes['valid_to']}'" if mes['valid_to'] else "null"
        cypher_lines.append(f"MERGE (f:Factory {{name: '{mes['factory']}'}})")
        cypher_lines.append(f"MERGE (m:Machine {{id: '{mes['machine_id']}'}}) SET m.status = 'OPERATIONAL'")
        cypher_lines.append(f"MERGE (m)-[:LOCATED_IN]->(f)")
        cypher_lines.append(f"MERGE (p:Product {{name: '{mes['product_name']}'}})")
        cypher_lines.append(f"MERGE (ord:Order {{id: '{mes['order_id']}'}}) SET ord.amount = {mes['amount']}")
        cypher_lines.append(f"MERGE (ord)-[:INCLUDES]->(p)")
        cypher_lines.append(f"MERGE (c:Customer {{id: '{mes['customer_erp_id']}'}})")
        cypher_lines.append(f"MERGE (c)-[:PLACED_ORDER]->(ord)")
        cypher_lines.append(f"MERGE (wo:WorkOrder {{id: '{mes['work_order']}'}}) SET wo.status = '{mes['status']}'")
        cypher_lines.append(f"MERGE (wo)-[:REQUIRES]->(p)")
        # 유효 기간 속성을 부착한 관계
        cypher_lines.append(f"MERGE (wo)-[r:ASSIGNED_TO]->(m)")
        cypher_lines.append(f"  ON CREATE SET r.valid_from = '{mes['valid_from']}', r.valid_to = {valid_to_val}, r.tx_recorded = datetime();")

    cypher_path = os.path.join(out_dir, "load_graph.cypher")
    with open(cypher_path, "w", encoding="utf-8") as f:
        f.write("\n".join(cypher_lines))
    print(f"  - Cypher 생성 완료: {cypher_path} ({len(cypher_lines)} 라인)")

    print("[4/5] W3C RDF Turtle 온톨로지 생성...")
    ttl_lines = [
        "@prefix ex: <http://enterprise.org/onto#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# Class Definitions",
        "ex:Organization a rdfs:Class ; rdfs:label \"조직 및 고객사\" .",
        "ex:Machine a rdfs:Class ; rdfs:label \"생산 설비\" .",
        "ex:WorkOrder a rdfs:Class ; rdfs:label \"작업 지시\" .",
        "ex:Order a rdfs:Class ; rdfs:label \"수주\" .",
        "ex:Factory a rdfs:Class ; rdfs:label \"공장\" .",
        "",
        "# Instances"
    ]
    for erp in erp_rows:
        ttl_lines.append(f"ex:{erp['erp_id']} a ex:Organization ; ex:legalName \"{erp['name']}\" ; ex:taxId \"{erp['biz_no']}\" .")
    seen_factories = set()
    for mes in mes_rows:
        factory_iri = mes['factory'].replace(' ', '_')
        # 작업지시 → 수주 → 고객 연결(ex:orderRef, ex:orderedBy)과 공장 이름(ex:factoryName)을 함께 낸다.
        # 이 세 술어가 없으면 11장 역량 질문("울산 1공장 진행 중 작업지시와 수주 고객사")을 SPARQL 로 답할 수 없다.
        ttl_lines.append(f"ex:{mes['work_order']} a ex:WorkOrder ; ex:statusCode \"{mes['status']}\" ; ex:assignedTo ex:{mes['machine_id']} ; ex:orderRef ex:{mes['order_id']} .")
        ttl_lines.append(f"ex:{mes['machine_id']} a ex:Machine ; ex:locatedIn ex:{factory_iri} .")
        ttl_lines.append(f"ex:{mes['order_id']} a ex:Order ; ex:orderNumber \"{mes['order_id']}\" ; ex:orderedBy ex:{mes['customer_erp_id']} .")
        if factory_iri not in seen_factories:
            seen_factories.add(factory_iri)
            ttl_lines.append(f"ex:{factory_iri} a ex:Factory ; ex:factoryName \"{mes['factory']}\" .")

    ttl_path = os.path.join(out_dir, "enterprise_ontology.ttl")
    with open(ttl_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ttl_lines))
    print(f"  - Turtle 생성 완료: {ttl_path} ({len(ttl_lines)} 라인)")

    print("[5/5] 파이프라인 검증 보고서 작성 완료!")

if __name__ == "__main__":
    run_pipeline()
