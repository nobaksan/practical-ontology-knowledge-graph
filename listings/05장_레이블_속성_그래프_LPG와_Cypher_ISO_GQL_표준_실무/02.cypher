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
  t.retryCount = coalesce(t.retryCount, 0) + 1;
