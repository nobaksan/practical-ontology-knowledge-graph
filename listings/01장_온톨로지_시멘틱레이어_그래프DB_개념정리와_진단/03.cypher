// 동일한 역추적 질의를 온톨로지 기반 Cypher 그래프 쿼리로 표현
MATCH (p:Part {partNo: 'P-10482'})-[r:USED_IN*1..5]->(l:Lot)
RETURN DISTINCT l.lotId, size(r) AS hops;
