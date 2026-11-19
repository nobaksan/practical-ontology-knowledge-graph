// 고객에서 출발하고 허브를 종착점으로 둔다
MATCH (c:Customer {name: "김민수"})-[:OWNS]->(src:Account)
WITH collect(src) AS 계좌들          // 집계로 계획을 끊어 고객 계좌를 먼저 확정한다
UNWIND 계좌들 AS src
MATCH (src)-[t:TRANSFERS]->(h:Account)
WHERE h.accNo = $h
RETURN count(t) AS 건수
