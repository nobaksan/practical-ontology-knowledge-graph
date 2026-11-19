// === 1. 제약조건 및 인덱스 생성 ===
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT machine_id IF NOT EXISTS FOR (m:Machine) REQUIRE m.id IS UNIQUE;
CREATE CONSTRAINT work_order_id IF NOT EXISTS FOR (wo:WorkOrder) REQUIRE wo.id IS UNIQUE;

// === 2. 노드 및 엣지 적재 ===
MERGE (c:Customer {id: 'ERP_CUST_101'}) SET c.name = '현대자동차(주)', c.bizNo = '101-81-00234', c.address = '울산광역시 북구 염포로 700';
MERGE (c:Customer {id: 'ERP_CUST_102'}) SET c.name = '기아 주식회사', c.bizNo = '202-82-11456', c.address = '서울특별시 서초구 헌릉로 12';
MERGE (c:Customer {id: 'ERP_CUST_103'}) SET c.name = '삼성전자(주)', c.bizNo = '303-83-22567', c.address = '경기도 수원시 영통구 삼성로 129';
MERGE (c:Customer {id: 'ERP_CUST_104'}) SET c.name = 'LG에너지솔루션', c.bizNo = '404-84-33678', c.address = '서울특별시 영등포구 여의대로 108';
MERGE (c:Customer {id: 'ERP_CUST_105'}) SET c.name = 'SK온(주)', c.bizNo = '505-85-44789', c.address = '서울특별시 종로구 종로 26';
MERGE (c:Customer {id: 'ERP_CUST_106'}) SET c.name = '글로벌정밀기계', c.bizNo = '606-86-55890', c.address = '경상남도 창원시 성산구 공단로 50';
MERGE (c:Customer {id: 'ERP_CUST_107'}) SET c.name = '한국부품테크', c.bizNo = '707-87-66901', c.address = '인천광역시 남동구 남동서로 200';
MERGE (f:Factory {name: '울산 1공장'})
MERGE (m:Machine {id: 'CNC-04'}) SET m.status = 'OPERATIONAL'
MERGE (m)-[:LOCATED_IN]->(f)
MERGE (p:Product {name: 'EV배터리팩 케이스'})
MERGE (ord:Order {id: 'ORD-2026-A'}) SET ord.amount = 1250000000
MERGE (ord)-[:INCLUDES]->(p)
MERGE (c:Customer {id: 'ERP_CUST_101'})
MERGE (c)-[:PLACED_ORDER]->(ord)
MERGE (wo:WorkOrder {id: 'WO-9021'}) SET wo.status = 'IN_PROGRESS'
MERGE (wo)-[:REQUIRES]->(p)
MERGE (wo)-[r:ASSIGNED_TO]->(m)
  ON CREATE SET r.valid_from = '2026-03-01T08:00:00Z', r.valid_to = null, r.tx_recorded = datetime();
MERGE (f:Factory {name: '화성 2공장'})
MERGE (m:Machine {id: 'PRESS-02'}) SET m.status = 'OPERATIONAL'
MERGE (m)-[:LOCATED_IN]->(f)
MERGE (p:Product {name: '차량용 알루미늄 샤시'})
MERGE (ord:Order {id: 'ORD-2026-B'}) SET ord.amount = 840000000
MERGE (ord)-[:INCLUDES]->(p)
MERGE (c:Customer {id: 'ERP_CUST_102'})
MERGE (c)-[:PLACED_ORDER]->(ord)
MERGE (wo:WorkOrder {id: 'WO-9022'}) SET wo.status = 'COMPLETED'
MERGE (wo)-[:REQUIRES]->(p)
MERGE (wo)-[r:ASSIGNED_TO]->(m)
  ON CREATE SET r.valid_from = '2026-02-10T08:00:00Z', r.valid_to = '2026-02-28T18:00:00Z', r.tx_recorded = datetime();
MERGE (f:Factory {name: '구미 1공장'})
MERGE (m:Machine {id: 'LASER-01'}) SET m.status = 'OPERATIONAL'
MERGE (m)-[:LOCATED_IN]->(f)
MERGE (p:Product {name: '서버용 방열 모듈'})
MERGE (ord:Order {id: 'ORD-2026-C'}) SET ord.amount = 2100000000
MERGE (ord)-[:INCLUDES]->(p)
MERGE (c:Customer {id: 'ERP_CUST_103'})
MERGE (c)-[:PLACED_ORDER]->(ord)
MERGE (wo:WorkOrder {id: 'WO-9023'}) SET wo.status = 'IN_PROGRESS'
MERGE (wo)-[:REQUIRES]->(p)
MERGE (wo)-[r:ASSIGNED_TO]->(m)
  ON CREATE SET r.valid_from = '2026-03-05T09:00:00Z', r.valid_to = null, r.tx_recorded = datetime();
MERGE (f:Factory {name: '울산 1공장'})
MERGE (m:Machine {id: 'CNC-07'}) SET m.status = 'OPERATIONAL'
MERGE (m)-[:LOCATED_IN]->(f)
MERGE (p:Product {name: '원통형 배터리 캔'})
MERGE (ord:Order {id: 'ORD-2026-D'}) SET ord.amount = 670000000
MERGE (ord)-[:INCLUDES]->(p)
MERGE (c:Customer {id: 'ERP_CUST_104'})
MERGE (c)-[:PLACED_ORDER]->(ord)
MERGE (wo:WorkOrder {id: 'WO-9024'}) SET wo.status = 'IDLE'
MERGE (wo)-[:REQUIRES]->(p)
MERGE (wo)-[r:ASSIGNED_TO]->(m)
  ON CREATE SET r.valid_from = '2026-03-10T08:00:00Z', r.valid_to = null, r.tx_recorded = datetime();