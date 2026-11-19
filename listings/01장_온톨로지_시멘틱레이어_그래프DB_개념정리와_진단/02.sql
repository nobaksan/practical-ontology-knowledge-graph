-- RDBMS에서 3단계 관계를 역추적하는 6중 JOIN SQL
SELECT DISTINCT l.lot_id
FROM part p
  JOIN part_equipment pe ON pe.part_id = p.id
  JOIN equipment e ON e.id = pe.equipment_id
  JOIN process_equipment px ON px.equipment_id = e.id
  JOIN process pr ON pr.id = px.process_id
  JOIN lot_process lp ON lp.process_id = pr.id
  JOIN lot l ON l.id = lp.lot_id
WHERE p.part_no = 'P-10482';
