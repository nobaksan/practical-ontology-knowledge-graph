-- 12장 실습: 사람이 손으로 쓴 정답 SQL. Auto Ontology 의 답과 대조한다.

\echo '## 1. 2026년 3월 매출 상위 고객 (매출 = 수주 금액 합계, 취소 SO_STAT 90 제외)'
SELECT c.cust_nm,
       SUM(d.amt) FILTER (WHERE h.so_stat <> '90') AS 취소_제외,
       SUM(d.amt)                                  AS 취소_포함,
       COUNT(DISTINCT h.so_no)                     AS 수주_건수
FROM erp.so_hdr h
JOIN erp.so_dtl d   USING (so_no)
JOIN erp.cust_mst c USING (cust_cd)
WHERE h.so_dt >= '2026-03-01' AND h.so_dt < '2026-04-01'
GROUP BY c.cust_nm
ORDER BY 취소_제외 DESC
LIMIT 5;

\echo '## 2. 공장별 검사 불량률 (불량 수량 / 샘플 수량)'
SELECT p.plant_nm,
       SUM(i.smpl_qty) AS 샘플,
       SUM(i.dfct_qty) AS 불량,
       ROUND(100.0 * SUM(i.dfct_qty) / SUM(i.smpl_qty), 2) AS 불량률_퍼센트
FROM qms.insp i
JOIN mes.lot  l  USING (lot_no)
JOIN mes.wo   w  USING (wo_no)
JOIN mes.line ln USING (line_cd)
JOIN mes.plant p USING (plant_cd)
GROUP BY p.plant_nm
ORDER BY p.plant_nm;

\echo '## 3. 입고 로트 RL-2026-0102 가 들어간 제품을 출하받은 고객'
SELECT c.cust_nm, COUNT(DISTINCT s.lot_no) AS 출하_로트
FROM mes.lot_comp lc
JOIN erp.ship s     USING (lot_no)
JOIN erp.so_hdr h   ON h.so_no = s.so_no
JOIN erp.cust_mst c USING (cust_cd)
WHERE lc.rcv_lot_no = 'RL-2026-0102'
GROUP BY c.cust_nm
ORDER BY 출하_로트 DESC, c.cust_nm;
