SELECT h.so_no, h.cust_cd, h.so_dt, SUM(d.amt) AS net_revenue
FROM factory.erp.so_hdr h
JOIN factory.erp.so_dtl d ON d.so_no = h.so_no
WHERE h.so_stat <> '90'
GROUP BY h.so_no, h.cust_cd, h.so_dt
