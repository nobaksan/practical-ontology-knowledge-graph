CREATE GRAPH TYPE FinancialGraphType AS {
  -- 1. 노드 타입 선언
  NODE TYPE CustomerType (
    LABEL Customer {
      name STRING,
      ssn  STRING,
      tier STRING
    }
  ),
  NODE TYPE AccountType (
    LABEL Account {
      accNo   STRING,
      balance DECIMAL(15,2),
      bank    STRING
    }
  ),

  -- 2. 엣지 타입 선언 (출발-도착 타입 및 엣지 속성 타입 강제)
  EDGE TYPE OwnsType (CustomerType)-[LABEL OWNS]->(AccountType),
  EDGE TYPE TransfersType (AccountType)-[
    LABEL TRANSFERS {
      amount    DECIMAL(15,2),
      timestamp TIMESTAMP,
      channel   STRING
    }
  ]->(AccountType)
}
