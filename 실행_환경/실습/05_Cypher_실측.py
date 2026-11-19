"""5장 실습: 이체 그래프로 MERGE 멱등성, 인덱스, 가변 길이 폭발, 슈퍼노드를 Neo4j 에서 실측한다."""
import random
import time

from neo4j import GraphDatabase
from neo4j.exceptions import ConstraintError

from 공통 import NEO4J_AUTH, NEO4J_URI, 기록기, 실행_환경_설명, 측정

기록 = 기록기("05장_Cypher_실측.txt")
성 = list("김이박최정강조윤장임한오서신권황안송류홍")
이름 = ["민준", "서연", "도윤", "하은", "시우", "지유", "주원", "서윤", "예준", "지민",
        "하준", "수아", "지호", "채원", "건우", "다은", "현우", "윤서", "우진", "민서"]


def db_hits(요약):
    def 합(p):
        return p.get("dbHits", 0) + sum(합(c) for c in p.get("children", []))
    return 합(요약.profile)


def 행수(요약):
    return 요약.profile.get("rows", 0)


def 개수(s):
    r = s.run("MATCH (n) WITH count(n) AS n MATCH ()-[r]->() RETURN n, count(r) AS r").single()
    return r["n"], r["r"]


def 적재(s, rnd):
    s.run("MATCH (n) CALL { WITH n DETACH DELETE n } IN TRANSACTIONS OF 50000 ROWS").consume()
    for r in s.run("SHOW CONSTRAINTS YIELD name RETURN name").data():
        s.run(f"DROP CONSTRAINT `{r['name']}`").consume()
    for r in s.run("SHOW INDEXES YIELD name, type WHERE type <> 'LOOKUP' RETURN name").data():
        s.run(f"DROP INDEX `{r['name']}` IF EXISTS").consume()

    고객 = []
    for i in range(20_000):
        while True:
            n = rnd.choice(성) + rnd.choice(이름)
            if n != "김민수":
                break
        고객.append({"cid": f"C{i:05d}", "name": n, "tier": rnd.choice(["GOLD", "SILVER", "BASIC"])})
    고객[777] = {"cid": "C00777", "name": "김민수", "tier": "GOLD"}
    계좌 = [{"accNo": f"{100 + i % 900}-{i:06d}", "cid": f"C{i // 2:05d}", "bank": rnd.choice(["한빛", "누리", "바른"])}
            for i in range(40_000)]
    이체 = []
    for i in range(200_000):
        a, b = rnd.sample(range(40_000), 2)
        이체.append({"tx": f"TX{i:07d}", "src": 계좌[a]["accNo"], "dst": 계좌[b]["accNo"],
                     "amount": rnd.choice([50_000, 300_000, 1_200_000, 5_000_000, 12_000_000]),
                     "time": f"{rnd.randrange(24):02d}:{rnd.randrange(60):02d}:{rnd.randrange(60):02d}"})

    s.run("CREATE CONSTRAINT acc_no IF NOT EXISTS FOR (a:Account) REQUIRE a.accNo IS UNIQUE").consume()
    s.run("CALL db.awaitIndexes()").consume()
    for i in range(0, len(고객), 10_000):
        s.run("UNWIND $v AS x CREATE (:Customer {cid: x.cid, name: x.name, tier: x.tier})", v=고객[i:i + 10_000]).consume()
    s.run("CREATE INDEX cust_cid IF NOT EXISTS FOR (c:Customer) ON (c.cid)").consume()
    s.run("CALL db.awaitIndexes()").consume()
    for i in range(0, len(계좌), 10_000):
        s.run("""UNWIND $v AS x MATCH (c:Customer {cid: x.cid})
                 CREATE (c)-[:OWNS]->(:Account {accNo: x.accNo, bank: x.bank})""", v=계좌[i:i + 10_000]).consume()
    for i in range(0, len(이체), 20_000):
        s.run("""UNWIND $v AS x MATCH (a:Account {accNo: x.src}), (b:Account {accNo: x.dst})
                 CREATE (a)-[:TRANSFERS {txId: x.tx, amount: x.amount, time: x.time}]->(b)""",
              v=이체[i:i + 20_000]).consume()
    s.run("DROP INDEX cust_cid").consume()  # 실험 2 를 위해 이름 인덱스가 없는 상태로 시작한다


MERGE_원문 = """
// 1. 출발 계좌와 도착 계좌를 독립적으로 먼저 MERGE
MERGE (src:Account {accNo: "110-123"})
MERGE (dst:Account {accNo: "3333-88"})

// 2. 두 계좌 간의 이체 엣지를 MERGE하며 관계 속성 부여
MERGE (src)-[t:TRANSFERS {txId: "TX-20260301-901"}]->(dst)
ON CREATE SET
  t.amount    = 5000000,
  t.timestamp = datetime(),
  t.channel   = "MOBILE_APP"
ON MATCH SET
  t.retryCount = coalesce(t.retryCount, 0) + 1
"""

CREATE_실수 = """
CREATE (src:Account {accNo: "110-999"})
CREATE (dst:Account {accNo: "3333-99"})
CREATE (src)-[:TRANSFERS {txId: "TX-20260301-902", amount: 5000000}]->(dst)
"""

고액_야간 = """
MATCH (c:Customer {name: "김민수"})-[:OWNS]->(src:Account)
      -[t:TRANSFERS]->(dst:Account)
WHERE t.amount >= 5000000
  AND t.time >= "02:00:00"
RETURN dst.accNo AS targetAcc,
       t.amount   AS amount,
       t.time     AS transferTime
ORDER BY t.amount DESC
"""

고액_야간_수정 = 고액_야간.replace('AND t.time >= "02:00:00"', 'AND t.time >= "02:00:00" AND t.time < "05:00:00"')


def main():
    rnd = random.Random(7)
    기록("# 5장 Cypher 실측")
    기록(f"실행 환경: {실행_환경_설명()}")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH, notifications_min_severity="OFF")
    with driver.session() as s:
        버전 = s.run("CALL dbms.components() YIELD name, versions, edition "
                     "RETURN name + ' ' + versions[0] + ' ' + edition AS v").single()["v"]
        기록(f"Neo4j: {버전}")
        시작 = time.perf_counter()
        적재(s, rnd)
        n, r = 개수(s)
        기록(f"적재: 노드 {n:,} · 관계 {r:,} ({time.perf_counter() - 시작:.1f}초)")

        기록("\n## 1. MERGE 는 몇 번 돌려도 같은 그래프를 만든다 (5.3.2)")
        for 회 in (1, 2, 3):
            s.run(MERGE_원문).consume()
            n, r = 개수(s)
            재시도 = s.run("MATCH ()-[t:TRANSFERS {txId:'TX-20260301-901'}]->() "
                          "RETURN count(t) AS c, t.retryCount AS k").single()
            기록(f"MERGE {회}회차: 노드 {n:,} · 관계 {r:,} · 해당 이체 {재시도['c']}건 · retryCount={재시도['k']}")
        for 회 in (1, 2):
            try:
                s.run(CREATE_실수).consume()
                c = s.run("MATCH (a:Account {accNo:'110-999'}) RETURN count(a) AS c").single()["c"]
                기록(f"CREATE {회}회차: 같은 번호 계좌 노드 {c}개")
            except ConstraintError as e:
                기록(f"CREATE {회}회차: 실패 — {e.code}")
                기록(f"  {e.message}")
        s.run("MATCH (a:Account) WHERE a.accNo IN ['110-123','3333-88','110-999','3333-99'] DETACH DELETE a").consume()

        기록("\n## 2. 심야 고액 이체 질의와 시작 노드 인덱스 (5.3.1)")
        def 보기(행):
            return ", ".join(f"{x['targetAcc']}({x['amount']:,}원 {x['transferTime']})" for x in 행)
        기록(f"상한 없음(02:00 이후) {len(행 := s.run(고액_야간).data())}행: {보기(행)}")
        기록(f"수정 조건(02:00~05:00) {len(행 := s.run(고액_야간_수정).data())}행: {보기(행)}")
        요약 = s.run("PROFILE " + 고액_야간_수정).consume()
        중앙, _ = 측정(lambda: s.run(고액_야간_수정).consume())
        기록(f"인덱스 없음: db hits {db_hits(요약):,} · 중앙값 {중앙:.2f}ms")
        s.run("CREATE INDEX cust_name IF NOT EXISTS FOR (c:Customer) ON (c.name)").consume()
        s.run("CALL db.awaitIndexes()").consume()
        요약 = s.run("PROFILE " + 고액_야간_수정).consume()
        중앙, _ = 측정(lambda: s.run(고액_야간_수정).consume())
        기록(f"인덱스 있음: db hits {db_hits(요약):,} · 중앙값 {중앙:.2f}ms")

        기록("\n## 3. 가변 길이 탐색의 경로 수와 도달 계좌 수 (5.3.3)")
        평균 = s.run("MATCH (a:Account) RETURN avg(COUNT { (a)-[:TRANSFERS]->() }) AS k").single()["k"]
        기록(f"계좌당 평균 출금 이체 수 k = {평균:.2f}")
        기록(f"{'깊이':<4} {'경로 수':>10} {'도달 계좌':>10} {'db hits':>12} {'시간(ms)':>10}")
        출발 = "100-000000"
        for 깊이 in range(1, 9):
            q = (f"MATCH p = (a:Account {{accNo: $acc}})-[:TRANSFERS*1..{깊이}]->(b:Account) "
                 "RETURN count(p) AS 경로, count(DISTINCT b) AS 도달")
            시작 = time.perf_counter()
            s.run(q, acc=출발).consume()  # 계획 수립 시간을 빼려고 한 번 먼저 돌린다
            시작 = time.perf_counter()
            r = s.run(q, acc=출발).single()
            걸린 = (time.perf_counter() - 시작) * 1000
            요약 = s.run("PROFILE " + q, acc=출발).consume()
            기록(f"{깊이:<6} {r['경로']:>10,} {r['도달']:>10,} {db_hits(요약):>12,} {걸린:>10.0f}")
            if 걸린 > 60_000:
                break

        기록("\n## 4. 슈퍼노드: 출발점이냐 종착점이냐 (5.5.3 전략 3)")
        허브 = "999-HUB000"
        s.run("CREATE (:Account {accNo: $h, bank: '한빛'})", h=허브).consume()
        s.run("""MATCH (h:Account {accNo: $h})
                 MATCH (a:Account) WHERE a.accNo <> $h
                 WITH h, a LIMIT 40000
                 UNWIND range(1, 5) AS i
                 CREATE (a)-[:TRANSFERS {txId: 'HUB-' + a.accNo + '-' + i, amount: 300000, time: '10:00:00'}]->(h)""",
              h=허브).consume()
        차수 = s.run("MATCH (h:Account {accNo: $h}) RETURN COUNT { (h)<-[:TRANSFERS]-() } AS d", h=허브).single()["d"]
        기록(f"허브 계좌로 들어오는 이체 {차수:,}건")
        질문 = "김민수 계좌가 허브 계좌로 돈을 보낸 적이 있는가"
        허브_출발 = """
MATCH (h:Account {accNo: $h})
WITH collect(h) AS 허브들            // 집계로 계획을 끊어 허브를 먼저 확정한다
UNWIND 허브들 AS h
MATCH (h)<-[t:TRANSFERS]-(src:Account)<-[:OWNS]-(c:Customer)
WHERE c.name = "김민수"
RETURN count(t) AS 건수"""
        고객_출발 = """
MATCH (c:Customer {name: "김민수"})-[:OWNS]->(src:Account)
WITH collect(src) AS 계좌들          // 집계로 계획을 끊어 고객 계좌를 먼저 확정한다
UNWIND 계좌들 AS src
MATCH (src)-[t:TRANSFERS]->(h:Account)
WHERE h.accNo = $h
RETURN count(t) AS 건수"""
        플래너 = """
MATCH (c:Customer {name: "김민수"})-[:OWNS]->(src:Account)-[t:TRANSFERS]->(h:Account {accNo: $h})
RETURN count(t) AS 건수"""
        기록(f"질문: {질문}")
        for 이름, q in [("허브에서 출발", 허브_출발), ("고객에서 출발", 고객_출발), ("플래너에 맡김", 플래너)]:
            건수 = s.run(q, h=허브).single()["건수"]
            요약 = s.run("PROFILE " + q, h=허브).consume()
            중앙, _ = 측정(lambda: s.run(q, h=허브).consume(), 반복=20)
            기록(f"{이름:<10} 건수 {건수} · db hits {db_hits(요약):>9,} · 중앙값 {중앙:7.2f}ms")
            if True:
                def 연산자(p, 깊이=0):
                    yield "  " * 깊이 + p["operatorType"].split("@")[0]
                    for c in p.get("children", []):
                        yield from 연산자(c, 깊이 + 1)
                기록("  실행 계획(아래에서 위로 실행):")
                for 줄 in 연산자(요약.profile):
                    기록("    " + 줄)

    driver.close()
    기록.저장()


if __name__ == "__main__":
    main()
