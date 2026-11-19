MATCH (c:Customer {name: "김민수"})-[:OWNS]->(src:Account)
      -[t:TRANSFERS]->(dst:Account)
WHERE t.amount >= 5000000
  AND t.time >= "02:00:00"
  AND t.time <  "05:00:00"
RETURN dst.accNo AS targetAcc,
       t.amount   AS amount,
       t.time     AS transferTime
ORDER BY t.amount DESC;
