-- RDBMS에서 3단계 관계를 추적하는 전형적인 6중 조인 SQL
SELECT DISTINCT l.lot_id
FROM part p                                  -- [0홉] 시작점: 단 1행 로드
  JOIN part_equipment pe ON pe.part_id = p.id
  JOIN equipment e ON e.id = pe.equipment_id -- [1홉] B-Tree 조회 ➔ 3행으로 증가
  JOIN process_equipment px ON px.equipment_id = e.id
  JOIN process pr ON pr.id = px.process_id   -- [2홉] B-Tree 조회 ➔ 9행으로 증가
  JOIN lot_process lp ON lp.process_id = pr.id
  JOIN lot l ON l.id = lp.lot_id             -- [3홉] B-Tree 조회 ➔ 27행 생성 후 DISTINCT 필터
WHERE p.part_no = 'P-10482';
