// 1. 노드 생성 및 엣지 자체에 속성 직접 기록
CREATE (src:Account {accNo: "110-123", bank: "Shinhan"}),
       (dst:Account {accNo: "3333-88", bank: "Kakao"}),
       (src)-[t:TRANSFERS {
         amount:    5000000,
         timestamp: "2026-03-01T02:15:30",
         channel:   "ATM"
       }]->(dst);

// 2. 단 2줄의 초간결 패턴 매칭 질의
MATCH (src:Account {accNo: "110-123"})-[t:TRANSFERS]->(dst:Account)
RETURN t.amount, t.timestamp;
