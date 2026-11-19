# 04장_W3C_시멘틱_웹_표준_실무_RDF_SPARQL_OWL_SHACL

본문에 실린 순서대로 코드 블록 15개를 그대로 옮겼다.

| 파일 | 절 | 언어 | 첫 줄 |
|---|---|---|---|
| [01.ttl](01.ttl) | 4.1.1 주어·술어·목적어의 세 조각: 테이블과 컬럼이 없는 스키마리스 모델 | turtle | `:eq_robot01  :installedIn  :line_assembly_A .` |
| [02.ttl](02.ttl) | 4.1.3 전역 식별자 IRI의 4대 엔지니어링 가치 | turtle | `@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .` |
| [03.ttl](03.ttl) | 4.1.5 관계에 속성을 부여하는 차세대 표준: RDF-Star(RDF 1.2) | turtle | `<< :eq_robot01 :installedIn :line_assembly_A >>` |
| [04.rq](04.rq) | 4.2.1 기본 그래프 패턴(BGP)과 변수 기반 자동 조인 메커니즘 | sparql | `PREFIX : <https://company.internal/ontology/manufacturing#>` |
| [05.rq](05.rq) | 4.2.2 속성 경로와 재귀 탐색, 엔드포인트 연합 질의(Federation) | sparql | `?equipment :installedIn / :belongsTo / :ownedBy ?corporation` |
| [06.rq](06.rq) | 4.2.2 속성 경로와 재귀 탐색, 엔드포인트 연합 질의(Federation) | sparql | `# 부품의 모든 상위 조립체를 끝까지 재귀 추적 (1회 이상)` |
| [07.rq](07.rq) | 4.2.2 속성 경로와 재귀 탐색, 엔드포인트 연합 질의(Federation) | sparql | `SELECT ?eqName ?chemName` |
| [08.ttl](08.ttl) | 4.4.2 NodeShape와 PropertyShape로 정의하는 데이터 형태 제약 | turtle | `@prefix sh:   <http://www.w3.org/ns/shacl#> .` |
| [09.ttl](09.ttl) | 4.4.3 표준 ValidationReport를 통한 무결성 위반 감지와 거버넌스 자동화 | turtle | `[ a sh:ValidationReport ;` |
| [10.sh](10.sh) | 4.6 실습: 공장 데이터 한 벌로 SPARQL, OWL, SHACL을 차례로 돌려 본다 | bash | `cd 실행_환경/실습` |
| [11.ttl](11.ttl) | 4.6 실습: 공장 데이터 한 벌로 SPARQL, OWL, SHACL을 차례로 돌려 본다 | turtle | `# 결함 데이터 두 건: 라인 정보 누락, 라인 자리에 공장을 넣음` |
| [12.txt](12.txt) | 4.6 실습: 공장 데이터 한 벌로 SPARQL, OWL, SHACL을 차례로 돌려 본다 | text | `[서울 공장 조립 설비] 2행` |
| [13.txt](13.txt) | 4.6 실습: 공장 데이터 한 벌로 SPARQL, OWL, SHACL을 차례로 돌려 본다 | text | `[추론 전: 상위 클래스 Equipment 로 찾기] 0행` |
| [14.txt](14.txt) | 4.6 실습: 공장 데이터 한 벌로 SPARQL, OWL, SHACL을 차례로 돌려 본다 | text | `[라인이 없는 설비 (FILTER NOT EXISTS 로 직접 찾아야 보인다)] 1행` |
| [15.ttl](15.ttl) | 4.6 실습: 공장 데이터 한 벌로 SPARQL, OWL, SHACL을 차례로 돌려 본다 | turtle | `[] a sh:ValidationReport ;` |
