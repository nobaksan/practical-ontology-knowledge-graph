"""4장 실습: 같은 공장 데이터로 SPARQL 속성 경로, OWL RL 추론, SHACL 검증을 차례로 돌린다."""
import time
from pathlib import Path

import owlrl
from pyshacl import validate
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, SH

from 공통 import 기록기, 실행_환경_설명

여기 = Path(__file__).resolve().parent / "04장"
M = Namespace("https://company.internal/ontology/manufacturing#")
머리 = "PREFIX : <https://company.internal/ontology/manufacturing#>\n" \
       "PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n"
기록 = 기록기("04장_RDF_추론_검증.txt")


def 짧게(v):
    return str(v).split("#")[-1]


def 질의(g, 제목, q):
    행 = list(g.query(머리 + q))
    기록(f"\n[{제목}] {len(행)}행")
    for r in 행:
        기록("  " + " | ".join(짧게(v) for v in r))
    return 행


기록("# 4장 RDF·SPARQL·OWL·SHACL 실습")
기록(f"실행 환경: {실행_환경_설명()}")

g = Graph().parse(여기 / "공장.ttl")
기록(f"\n원본 트리플 {len(g)}개")

기록("\n## 1. 기본 그래프 패턴 (4.2.1 질의 그대로)")
질의(g, "서울 공장 조립 설비", """
SELECT ?equipment ?eqName ?lineName
WHERE {
  ?equipment a :AssemblyEquipment ;
             :hasName ?eqName ;
             :installedIn ?line .
  ?line :belongsTo :Factory_Seoul ;
        :hasName ?lineName .
}""")

기록("\n## 2. 속성 경로 (4.2.2)")
질의(g, "설비 → 라인 → 공장 → 법인 순차 경로", """
SELECT ?equipment ?corp WHERE { ?equipment :installedIn/:belongsTo/:ownedBy ?corp . }
ORDER BY ?equipment""")
질의(g, "센서의 모든 상위 소속 (partOf+)", """
SELECT ?root WHERE { :sensor01 :partOf+ ?root . }""")

기록("\n## 3. 추론 전후 비교 (4.3.1)")
상위질의 = "SELECT ?eq WHERE { ?eq a :Equipment . } ORDER BY ?eq"
질의(g, "추론 전: 상위 클래스 Equipment 로 찾기", 상위질의)

추론 = Graph()
for t in g:
    추론.add(t)
시작 = time.perf_counter()
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(추론)
걸린 = (time.perf_counter() - 시작) * 1000
기록(f"\nOWL 2 RL 물체화: {len(g)} → {len(추론)} 트리플 (+{len(추론) - len(g)}, {걸린:.0f}ms)")

질의(추론, "추론 후: 상위 클래스 Equipment 로 찾기", 상위질의)
질의(추론, "역관계: 조립 A 라인이 가진 설비 (hasEquipment 는 적재한 적 없음)",
     "SELECT ?eq WHERE { :line_assembly_A :hasEquipment ?eq . }")
질의(추론, "전이성: 센서가 바로 소속된 대상 (partOf 한 단계)",
     "SELECT ?x WHERE { :sensor01 :partOf ?x . } ORDER BY ?x")
질의(추론, "동등성: ERP 번호로 MES 온도 읽기",
     "SELECT ?asset ?temp WHERE { :eq_erp_101 :assetNo ?asset ; :lastTemp ?temp . }")

기록("\n## 4. OWL 은 결함을 잡지 않는다 (4.3.3)")
기록("공장.ttl 에는 '설비는 installedIn 을 1개 이상' 이라는 owl:minCardinality 공리가 있다.")
질의(추론, "라인이 없는 설비 (FILTER NOT EXISTS 로 직접 찾아야 보인다)", """
SELECT ?eq WHERE { ?eq a :Equipment . FILTER NOT EXISTS { ?eq :installedIn ?l } }""")
오류 = "http://www.daml.org/2002/03/agents/agent-ont#error"
기록(f"추론기가 남긴 오류 메시지: {len(list(추론.objects(predicate=URIRef(오류))))}건")

대조 = Graph()
for t in g:
    대조.add(t)
대조.add((M.eq_erp_101, OWL.differentFrom, M.eq_mes_909))
owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(대조)
메시지 = sorted(set(str(m) for m in 대조.objects(predicate=URIRef(오류))))
기록(f"대조: sameAs 와 differentFrom 을 함께 선언하면 오류 {len(메시지)}건")
기록("  " + 메시지[0].split(":")[0] if 메시지 else "  (없음)")

기록("\n## 5. SHACL 검증 (4.4.2 셰이프 그대로)")
셰이프 = Graph().parse(여기 / "셰이프.ttl")
for 이름, 데이터 in [("추론 전 원본", g), ("OWL 추론 후", 추론)]:
    시작 = time.perf_counter()
    적합, 보고, 글 = validate(데이터, shacl_graph=셰이프, inference="none")
    걸린 = (time.perf_counter() - 시작) * 1000
    결과 = list(보고.subjects(predicate=None, object=SH.ValidationResult))
    기록(f"\n[{이름}] conforms={적합} · 위반 {len(결과)}건 · {걸린:.0f}ms")
    줄 = []
    for r in 결과:
        초점 = 짧게(보고.value(r, SH.focusNode))
        경로 = 짧게(보고.value(r, SH.resultPath))
        구성 = 짧게(보고.value(r, SH.sourceConstraintComponent)).split("/")[-1]
        값 = 보고.value(r, SH.value)
        줄.append(f"  {초점:<11} {경로:<12} {구성:<34} value={짧게(값) if 값 else '-'}")
    for x in sorted(줄):
        기록(x)
    if 이름 == "OWL 추론 후":
        (Path(__file__).resolve().parent / "결과" / "04장_SHACL_보고서.ttl").write_text(
            보고.serialize(format="turtle"), encoding="utf-8")

기록.저장()
