"""11장 5절: 같은 역량 질문을 Fuseki SPARQL 과 Neo4j Cypher 로 돌려 결과 행과 지연을 잰다.

먼저 할 일(11장 본문 2~5절):
  - docker compose up -d neo4j fuseki
  - python3 실행_환경/코드/pipeline_runner.py
  - Neo4j 에 검증_근거/load_graph.cypher 적재
  - Fuseki 에 데이터셋 onto(TDB2)를 만들고 검증_근거/enterprise_ontology.ttl 적재

지연은 클라이언트에서 잰 왕복 시간이다(HTTP 또는 Bolt 왕복 + 질의 실행).
데이터가 작아(트리플 73개, 노드 26개) 엔진 성능 비교로 읽으면 안 된다.
"""
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import rdflib
from neo4j import GraphDatabase

from 공통 import NEO4J_AUTH, NEO4J_URI, 결과_폴더, 실행_환경_설명, 측정

FUSEKI = os.environ.get("ONTO_FUSEKI_URL", "http://localhost:3030/onto/sparql")
TTL = Path(__file__).resolve().parents[1] / "검증_근거" / "enterprise_ontology.ttl"

SPARQL = """PREFIX ex: <http://enterprise.org/onto#>

SELECT ?custName ?orderNo ?workOrder WHERE {
  ?factory a ex:Factory ;
           ex:factoryName "울산 1공장" .
  ?machine ex:locatedIn ?factory .
  ?wo ex:assignedTo ?machine ;
      ex:statusCode "IN_PROGRESS" ;
      ex:orderRef ?order .
  ?order ex:orderNumber ?orderNo ;
         ex:orderedBy ?customer .
  ?customer ex:legalName ?custName .
  BIND(STRAFTER(STR(?wo), "#") AS ?workOrder)
}"""

CYPHER = """MATCH (f:Factory {name: "울산 1공장"})<-[:LOCATED_IN]-(m:Machine)
      <-[:ASSIGNED_TO]-(wo:WorkOrder {status: "IN_PROGRESS"})
      -[:REQUIRES]->(p:Product)<-[:INCLUDES]-(ord:Order)
      <-[:PLACED_ORDER]-(c:Customer)
RETURN c.name AS custName, ord.id AS orderNo, wo.id AS workOrder"""


def fuseki_질의():
    data = urllib.parse.urlencode({"query": SPARQL}).encode()
    req = urllib.request.Request(FUSEKI, data=data, headers={"Accept": "text/csv"})
    with urllib.request.urlopen(req) as r:
        rows = r.read().decode("utf-8").strip().splitlines()
    return [tuple(x.split(",")) for x in rows[1:]]


def main():
    out = [f"# 11장 CQ 실측 · {실행_환경_설명()}", ""]

    g = rdflib.Graph().parse(TTL, format="turtle")
    로컬 = [tuple(str(v) for v in row) for row in g.query(SPARQL)]
    out.append(f"[rdflib] 트리플 {len(g)} · 결과 {len(로컬)}행 {로컬}")

    원격 = fuseki_질의()
    out.append(f"[Fuseki] 결과 {len(원격)}행 {원격}")

    with GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH) as drv:
        with drv.session() as s:
            노드 = s.run("MATCH (n) RETURN count(n) AS n").single()["n"]
            cy = [tuple(r.values()) for r in s.run(CYPHER)]
            out.append(f"[Neo4j] 노드 {노드} · 결과 {len(cy)}행 {cy}")
            neo_med, neo_p95 = 측정(lambda: list(s.run(CYPHER)), 반복=50, 예열=10)

    fu_med, fu_p95 = 측정(fuseki_질의, 반복=50, 예열=10)
    out += [
        "",
        "지연(클라이언트 왕복, 예열 10회 뒤 50회)",
        f"  Fuseki SPARQL (HTTP)  중앙값 {fu_med:.2f}ms · p95 {fu_p95:.2f}ms",
        f"  Neo4j  Cypher (Bolt)  중앙값 {neo_med:.2f}ms · p95 {neo_p95:.2f}ms",
    ]
    text = "\n".join(out)
    print(text)
    (결과_폴더 / "11장_CQ_실측.txt").write_text(text + "\n", encoding="utf-8")
    sys.exit(0 if len(로컬) == len(원격) == len(cy) == 1 else 1)


if __name__ == "__main__":
    main()
