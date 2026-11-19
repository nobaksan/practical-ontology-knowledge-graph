MATCH path = (c:Customer)-[:PLACED_ORDER]->(ord:Order)
             -[:INCLUDES]->(p:Product)
             <-[:REQUIRES]-(wo:WorkOrder)
             -[r:ASSIGNED_TO]->(m:Machine)
             -[:LOCATED_IN]->(f:Factory)
RETURN path LIMIT 25;
