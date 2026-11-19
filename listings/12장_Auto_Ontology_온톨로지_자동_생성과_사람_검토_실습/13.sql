SELECT p.plant_cd, p.plant_nm,
       CAST(SUM(i.dfct_qty) AS REAL) / CAST(SUM(i.smpl_qty) AS REAL) AS defect_rate
FROM factory.qms.insp i
JOIN factory.mes.lot l ON l.lot_no = i.lot_no
JOIN factory.mes.wo w ON w.wo_no = l.wo_no
JOIN factory.mes.line ln ON ln.line_cd = w.line_cd
JOIN factory.mes.plant p ON p.plant_cd = ln.plant_cd
GROUP BY p.plant_cd, p.plant_nm
ORDER BY p.plant_cd;
