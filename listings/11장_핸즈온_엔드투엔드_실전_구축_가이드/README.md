# 11장_핸즈온_엔드투엔드_실전_구축_가이드

본문에 실린 순서대로 코드 블록 15개를 그대로 옮겼다.

| 파일 | 절 | 언어 | 첫 줄 |
|---|---|---|---|
| [01.yml](01.yml) | 2. Docker Compose 기반 로컬 인프라 프로비저닝 | yaml | `version: '3.8'` |
| [02.sh](02.sh) | 2. Docker Compose 기반 로컬 인프라 프로비저닝 | bash | `cd 실행_환경/docker` |
| [03.sh](03.sh) | 3. 원천 데이터 생성과 엔티티 리졸루션 파이프라인 가동 | bash | `python3 실행_환경/실측_데이터/generate_sample_data.py` |
| [04.sh](04.sh) | 3. 원천 데이터 생성과 엔티티 리졸루션 파이프라인 가동 | bash | `python3 실행_환경/코드/pipeline_runner.py` |
| [05.txt](05.txt) | 3. 원천 데이터 생성과 엔티티 리졸루션 파이프라인 가동 | text | `[1/5] 원천 데이터 로드 및 정규화...` |
| [06.sh](06.sh) | 4. Neo4j 적재와 통합 지식그래프 서브그래프 시각화 | bash | `docker exec -i -e LANG=C.UTF-8 onto-neo4j cypher-shell -u ne` |
| [07.cypher](07.cypher) | 4. Neo4j 적재와 통합 지식그래프 서브그래프 시각화 | cypher | `MATCH path = (c:Customer)-[:PLACED_ORDER]->(ord:Order)` |
| [08.sh](08.sh) | 5. 실측: SPARQL과 Cypher로 같은 역량 질문 풀기 | bash | `curl -u admin:admin -X POST 'http://localhost:3030/$/dataset` |
| [09.rq](09.rq) | 5. 실측: SPARQL과 Cypher로 같은 역량 질문 풀기 | sparql | `PREFIX ex: <http://enterprise.org/onto#>` |
| [10.sh](10.sh) | 5. 실측: SPARQL과 Cypher로 같은 역량 질문 풀기 | bash | `curl -s http://localhost:3030/onto/sparql -H 'Accept: text/c` |
| [11.txt](11.txt) | 5. 실측: SPARQL과 Cypher로 같은 역량 질문 풀기 | text | `custName,orderNo,workOrder` |
| [12.cypher](12.cypher) | 5. 실측: SPARQL과 Cypher로 같은 역량 질문 풀기 | cypher | `MATCH (f:Factory {name: "울산 1공장"})<-[:LOCATED_IN]-(m:Machine` |
| [13.txt](13.txt) | 5. 실측: SPARQL과 Cypher로 같은 역량 질문 풀기 | text | `custName, orderNo, workOrder` |
| [14.sh](14.sh) | 6. GraphRAG AI 에이전트 CLI 구동과 팩트 앵커링 검증 | bash | `python3 실행_환경/코드/graphrag_subgraph_packer.py "현대자동차의 배터리팩 수주` |
| [15.txt](15.txt) | 6. GraphRAG AI 에이전트 CLI 구동과 팩트 앵커링 검증 | text | `[CLI] 사용자 질문 수신: "현대자동차의 배터리팩 수주와 관련된 현재 설비 가동 상태와 위험 요소를 알려` |
