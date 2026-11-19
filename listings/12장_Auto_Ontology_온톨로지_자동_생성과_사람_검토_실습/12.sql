SELECT c.cust_nm AS customer_name, SUM(d.amt) AS total_sales
FROM factory.erp.so_hdr h
JOIN factory.erp.so_dtl d ON d.so_no = h.so_no
JOIN factory.erp.cust_mst c ON c.cust_cd = h.cust_cd
WHERE h.so_dt >= '2026-03-01' AND h.so_dt < '2026-04-01'
  AND h.so_stat <> '90'
GROUP BY c.cust_nm
ORDER BY total_sales DESC
LIMIT 3;
