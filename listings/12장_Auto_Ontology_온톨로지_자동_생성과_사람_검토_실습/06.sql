SELECT CAST(SUM(d.dfct_qty) AS REAL) / SUM(i.smpl_qty) * 100 AS defect_rate
FROM factory.qms.insp_dfct d
JOIN factory.qms.insp i ON d.insp_no = i.insp_no
