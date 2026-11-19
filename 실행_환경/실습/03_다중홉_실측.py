"""3장 실습: 부품 → 설비 → 공정 → 로트 역추적을 SQL 조인·재귀 CTE·Cypher 로 실측한다.

사용법:
    python 03_다중홉_실측.py --배율 1     # 부품 2만 개 규모
    python 03_다중홉_실측.py --배율 10    # 부품 20만 개 규모(데이터만 10배, 질문은 같다)
"""
import argparse
import random
import time

import psycopg
from neo4j import GraphDatabase

from 공통 import NEO4J_AUTH, NEO4J_URI, PG_DSN, 기록기, 실행_환경_설명, 측정

분기 = 10  # 홉마다 평균 연결 수 k
대상_부품 = "P-10482"


def 데이터_생성(배율, 씨앗=42):
    rnd = random.Random(씨앗)
    부품 = [f"P-{i:06d}" for i in range(20_000 * 배율)]
    부품[10482] = 대상_부품
    설비 = [f"EQ-{i:06d}" for i in range(2_000 * 배율)]
    공정 = [f"PR-{i:06d}" for i in range(5_000 * 배율)]
    로트 = [f"LOT-{i:07d}" for i in range(50_000 * 배율)]
    부품_설비 = [(p, e) for p in 부품 for e in rnd.sample(설비, 분기)]
    설비_공정 = [(e, pr) for e in 설비 for pr in rnd.sample(공정, 분기)]
    공정_로트 = [(pr, l) for pr in 공정 for l in rnd.sample(로트, 분기)]
    return 부품, 설비, 공정, 로트, 부품_설비, 설비_공정, 공정_로트


SQL_조인 = """
SELECT DISTINCT l.lot_id
FROM part p
  JOIN part_equipment pe   ON pe.part_id = p.id
  JOIN equipment e         ON e.id = pe.equipment_id
  JOIN process_equipment px ON px.equipment_id = e.id
  JOIN process pr          ON pr.id = px.process_id
  JOIN lot_process lp      ON lp.process_id = pr.id
  JOIN lot l               ON l.id = lp.lot_id
WHERE p.part_no = %s
"""

SQL_재귀 = """
WITH RECURSIVE 경로(노드, 깊이) AS (
  SELECT %s::text, 0
  UNION ALL
  SELECT k.dst, 경로.깊이 + 1
  FROM 경로 JOIN link k ON k.src = 경로.노드
  WHERE 경로.깊이 < 4
)
SELECT DISTINCT 노드 FROM 경로 WHERE 노드 LIKE 'LOT-%%'
"""

CYPHER_경로 = """
MATCH path = (p:Part {partNo: $partNo})-[:USED_IN*1..4]->(l:Lot)
RETURN l.lotId AS targetLot, length(path) AS hops,
       [n IN nodes(path) | n.name] AS traversalRoute
"""

CYPHER_고유 = """
MATCH (p:Part {partNo: $partNo})-[:USED_IN*1..4]->(l:Lot)
RETURN count(DISTINCT l) AS 고유_로트
"""


def pg_적재(conn, 데이터, 기록):
    부품, 설비, 공정, 로트, 부품_설비, 설비_공정, 공정_로트 = 데이터
    시작 = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS part_equipment, process_equipment, lot_process,
                                 part, equipment, process, lot, link;
            CREATE TABLE part      (id serial PRIMARY KEY, part_no text UNIQUE);
            CREATE TABLE equipment (id serial PRIMARY KEY, code text UNIQUE);
            CREATE TABLE process   (id serial PRIMARY KEY, code text UNIQUE);
            CREATE TABLE lot       (id serial PRIMARY KEY, lot_id text UNIQUE);
            CREATE TABLE part_equipment    (part_id int, equipment_id int);
            CREATE TABLE process_equipment (equipment_id int, process_id int);
            CREATE TABLE lot_process       (process_id int, lot_id int);
            CREATE TABLE link (src text, dst text);
        """)
        for 표, 열, 값 in [("part", "part_no", 부품), ("equipment", "code", 설비),
                          ("process", "code", 공정), ("lot", "lot_id", 로트)]:
            with cur.copy(f"COPY {표} ({열}) FROM STDIN") as cp:
                for v in 값:
                    cp.write_row((v,))
        # 이름 → 일련번호 대응표를 만들어 브리지 테이블을 채운다
        def 번호(표, 열):
            cur.execute(f"SELECT {열}, id FROM {표}")
            return dict(cur.fetchall())
        p_id, e_id = 번호("part", "part_no"), 번호("equipment", "code")
        pr_id, l_id = 번호("process", "code"), 번호("lot", "lot_id")
        for 표, 열, 쌍, a, b in [
            ("part_equipment", "(part_id, equipment_id)", 부품_설비, p_id, e_id),
            ("process_equipment", "(equipment_id, process_id)", 설비_공정, e_id, pr_id),
            ("lot_process", "(process_id, lot_id)", 공정_로트, pr_id, l_id),
        ]:
            with cur.copy(f"COPY {표} {열} FROM STDIN") as cp:
                for x, y in 쌍:
                    cp.write_row((a[x], b[y]))
        with cur.copy("COPY link (src, dst) FROM STDIN") as cp:
            for 쌍 in (부품_설비, 설비_공정, 공정_로트):
                for x, y in 쌍:
                    cp.write_row((x, y))
        # 외래키 방향마다 인덱스를 둔다(관계형 쪽에 최선의 조건을 준다)
        cur.execute("""
            CREATE INDEX ON part_equipment (part_id);
            CREATE INDEX ON process_equipment (equipment_id);
            CREATE INDEX ON lot_process (process_id);
            CREATE INDEX ON link (src);
            ANALYZE;
        """)
    conn.commit()
    기록(f"Postgres 적재 {time.perf_counter() - 시작:.1f}초")


def neo4j_적재(driver, 데이터, 기록):
    부품, 설비, 공정, 로트, 부품_설비, 설비_공정, 공정_로트 = 데이터
    시작 = time.perf_counter()
    with driver.session() as s:
        s.run("MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 50000 ROWS").consume()
        for 라벨, 키 in [("Part", "partNo"), ("Equipment", "code"), ("Process", "code"), ("Lot", "lotId")]:
            s.run(f"CREATE CONSTRAINT IF NOT EXISTS FOR (n:{라벨}) REQUIRE n.{키} IS UNIQUE").consume()
        s.run("CALL db.awaitIndexes()").consume()

        def 노드(라벨, 키, 값):
            for i in range(0, len(값), 20_000):
                s.run(f"UNWIND $v AS x CREATE (:{라벨} {{{키}: x, name: x}})", v=값[i:i + 20_000]).consume()

        노드("Part", "partNo", 부품)
        노드("Equipment", "code", 설비)
        노드("Process", "code", 공정)
        노드("Lot", "lotId", 로트)

        def 관계(a라벨, a키, b라벨, b키, 쌍):
            for i in range(0, len(쌍), 20_000):
                s.run(f"""UNWIND $r AS r
                          MATCH (a:{a라벨} {{{a키}: r[0]}}), (b:{b라벨} {{{b키}: r[1]}})
                          CREATE (a)-[:USED_IN]->(b)""", r=쌍[i:i + 20_000]).consume()

        관계("Part", "partNo", "Equipment", "code", 부품_설비)
        관계("Equipment", "code", "Process", "code", 설비_공정)
        관계("Process", "code", "Lot", "lotId", 공정_로트)
    기록(f"Neo4j 적재 {time.perf_counter() - 시작:.1f}초")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--배율", type=int, default=1)
    배율 = ap.parse_args().배율
    기록 = 기록기(f"03장_다중홉_배율{배율}.txt")
    기록(f"# 3장 다중 홉 실측 — 배율 {배율}")
    기록(f"실행 환경: {실행_환경_설명()}")

    데이터 = 데이터_생성(배율)
    부품, 설비, 공정, 로트, 부품_설비, 설비_공정, 공정_로트 = 데이터
    기록(f"노드: 부품 {len(부품):,} · 설비 {len(설비):,} · 공정 {len(공정):,} · 로트 {len(로트):,}")
    기록(f"관계: {len(부품_설비) + len(설비_공정) + len(공정_로트):,}개 (홉마다 k={분기})")

    conn = psycopg.connect(PG_DSN)
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    pg_적재(conn, 데이터, 기록)
    neo4j_적재(driver, 데이터, 기록)

    기록("\n## 홉마다 불어나는 중간 행")
    with conn.cursor() as cur:
        단계 = [
            ("1홉 설비", "SELECT count(*) FROM part p JOIN part_equipment pe ON pe.part_id=p.id WHERE p.part_no=%s"),
            ("2홉 공정", "SELECT count(*) FROM part p JOIN part_equipment pe ON pe.part_id=p.id "
                        "JOIN process_equipment px ON px.equipment_id=pe.equipment_id WHERE p.part_no=%s"),
            ("3홉 로트", "SELECT count(*) FROM part p JOIN part_equipment pe ON pe.part_id=p.id "
                        "JOIN process_equipment px ON px.equipment_id=pe.equipment_id "
                        "JOIN lot_process lp ON lp.process_id=px.process_id WHERE p.part_no=%s"),
        ]
        for 이름, q in 단계:
            cur.execute(q, (대상_부품,))
            기록(f"{이름:<8} 중간 행 {cur.fetchone()[0]:>6,}")
        cur.execute(SQL_조인, (대상_부품,))
        고유 = len(cur.fetchall())
        기록(f"DISTINCT 후 고유 로트 {고유:,}")
        cur.execute(SQL_재귀, (대상_부품,))
        기록(f"재귀 CTE 고유 로트 {len(cur.fetchall()):,}")

    with driver.session() as s:
        r = s.run(CYPHER_고유, partNo=대상_부품).single()
        기록(f"Cypher 고유 로트 {r['고유_로트']:,}")
        경로 = s.run(CYPHER_경로, partNo=대상_부품).data()
        기록(f"Cypher 반환 경로 {len(경로):,}개, 예: {' → '.join(경로[0]['traversalRoute'])}")
        요약 = s.run("PROFILE " + CYPHER_고유, partNo=대상_부품).consume()
        def 합계(계획):
            return 계획.get("dbHits", 0) + sum(합계(c) for c in 계획.get("children", []))
        기록(f"Cypher PROFILE 총 db hits {합계(요약.profile):,}")

    기록("\n## 응답 시간 (예열 5회 뒤 30회, 단위 ms)")
    with conn.cursor() as cur:
        def sql조인():
            cur.execute(SQL_조인, (대상_부품,)); cur.fetchall()
        def sql재귀():
            cur.execute(SQL_재귀, (대상_부품,)); cur.fetchall()
        for 이름, f in [("SQL 6중 조인", sql조인), ("SQL 재귀 CTE", sql재귀)]:
            중앙, p95 = 측정(f)
            기록(f"{이름:<14} 중앙값 {중앙:7.2f}  p95 {p95:7.2f}")
    with driver.session() as s:
        def cy고유():
            s.run(CYPHER_고유, partNo=대상_부품).consume()
        def cy경로():
            s.run(CYPHER_경로, partNo=대상_부품).data()
        for 이름, f in [("Cypher 고유 로트", cy고유), ("Cypher 경로 반환", cy경로)]:
            중앙, p95 = 측정(f)
            기록(f"{이름:<14} 중앙값 {중앙:7.2f}  p95 {p95:7.2f}")

    conn.close()
    driver.close()
    기록.저장()


if __name__ == "__main__":
    main()
