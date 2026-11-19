cd 실행_환경/docker
docker compose up -d neo4j postgres        # Neo4j 7687 포트, PostgreSQL 55432 포트
cd ../실습
uv venv .venv && uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/python 03_다중홉_실측.py --배율 1
.venv/bin/python 03_다중홉_실측.py --배율 10
