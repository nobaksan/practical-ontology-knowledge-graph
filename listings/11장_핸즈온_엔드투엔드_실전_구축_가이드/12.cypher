MATCH (f:Factory {name: "울산 1공장"})<-[:LOCATED_IN]-(m:Machine)
      <-[:ASSIGNED_TO]-(wo:WorkOrder {status: "IN_PROGRESS"})
      -[:REQUIRES]->(p:Product)<-[:INCLUDES]-(ord:Order)
      <-[:PLACED_ORDER]-(c:Customer)
RETURN c.name AS custName, ord.id AS orderNo, wo.id AS workOrder;
