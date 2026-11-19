SELECT c.cust_nm, COUNT(DISTINCT s.lot_no) AS 출하_로트
FROM mes.lot_comp lc
JOIN erp.ship s     USING (lot_no)
JOIN erp.so_hdr h   ON h.so_no = s.so_no
JOIN erp.cust_mst c USING (cust_cd)
WHERE lc.rcv_lot_no = 'RL-2026-0102'
GROUP BY c.cust_nm
ORDER BY 출하_로트 DESC, c.cust_nm;
