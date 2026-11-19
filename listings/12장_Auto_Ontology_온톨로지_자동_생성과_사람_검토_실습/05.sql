SELECT c.cust_nm, COUNT(s.so_no) AS total_sales
FROM factory.erp.so_hdr s
JOIN factory.erp.cust_mst c ON s.cust_cd = c.cust_cd
WHERE s.so_dt >= '2026-03-01' AND s.so_dt < '2026-04-01'
GROUP BY c.cust_nm
ORDER BY total_sales DESC
LIMIT 3;
