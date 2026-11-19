SELECT DISTINCT c.cust_cd
FROM factory.qms.rcv_lot AS r
JOIN factory.erp.item_mst AS i ON r.item_cd = i.item_cd
JOIN factory.erp.so_dtl AS s ON i.item_cd = s.item_cd
JOIN factory.erp.so_hdr AS h ON s.so_no = h.so_no
JOIN factory.erp.cust_mst AS c ON h.cust_cd = c.cust_cd
WHERE r.rcv_lot_no = 'RL-2026-0102';
