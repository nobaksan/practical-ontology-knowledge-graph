// 동일한 제조 역추적 질의를 Cypher로 표현
MATCH path = (p:Part {partNo: 'P-10482'})-[r:USED_IN*1..4]->(l:Lot)
RETURN 
  l.lotId AS targetLot,
  length(path) AS hops,
  [n IN nodes(path) | n.name] AS traversalRoute;
