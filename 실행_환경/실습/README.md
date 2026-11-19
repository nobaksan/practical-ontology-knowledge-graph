# 장별 실습

책 3·4·5장 끝의 실습 절이 쓰는 스크립트다. 결과 파일(`결과/`)은 2026-11-08 Apple M5 · Docker Desktop 에서 돌린 실제 출력이다.

```bash
cd ../docker && docker compose up -d neo4j postgres   # Neo4j 7687, Postgres 55432
cd ../실습
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt

.venv/bin/python 03_다중홉_실측.py --배율 1    # 3장: SQL 조인 · 재귀 CTE · Cypher
.venv/bin/python 03_다중홉_실측.py --배율 10
.venv/bin/python 04_RDF_추론_검증.py           # 4장: SPARQL · OWL RL · SHACL (DB 불필요)
.venv/bin/python 05_Cypher_실측.py             # 5장: MERGE · 인덱스 · 가변 길이 · 슈퍼노드
```

3장과 5장 스크립트는 시작할 때 Neo4j 의 기존 데이터를 지운다. 접속 정보는 `공통.py` 에 있고 환경 변수 `ONTO_PG_DSN`, `ONTO_NEO4J_URI`, `ONTO_NEO4J_PASSWORD` 로 바꿀 수 있다.
