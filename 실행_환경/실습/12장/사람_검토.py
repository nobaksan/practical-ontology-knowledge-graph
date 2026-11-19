"""12장 실습: 자동 생성된 온톨로지를 사람이 검토해 고치고 인증한다.

AI 가 만든 초안에 사람이 세 가지를 더한다.
  1. 용어: 이름과 설명을 업무 언어로 고치고 인증한다.
  2. SQL 속성: "매출"처럼 정의가 갈리는 지표와, 자동 추론이 놓친 연결을 SQL 로 못 박고 인증한다.
  3. 사용자 지시문: 업무 규칙과 "없는 데이터는 대신하지 말 것"을 에이전트에 알려 준다.

사용법: python 사람_검토.py           (같은 이름의 SQL 속성·지시문이 있으면 건너뛴다)
"""
import json
import os
import urllib.error
import urllib.request

API = os.environ.get("AUTO_ONTOLOGY_API_URL", "http://localhost:3000")
H = {"x-api-key": os.environ["AUTO_ONTOLOGY_API_TOKEN"], "Content-Type": "application/json"}


def 호출(방식, 경로, 본문=None):
    요청 = urllib.request.Request(API + 경로, method=방식, headers=H,
                                data=json.dumps(본문).encode() if 본문 is not None else None)
    try:
        with urllib.request.urlopen(요청) as r:
            내용 = r.read()
            return json.loads(내용) if 내용 else {}
    except urllib.error.HTTPError as e:
        raise SystemExit(f"{방식} {경로} → {e.code} {e.read()[:300].decode(errors='replace')}")


def 테이블별_용어():
    """용어 이름은 컴파일마다 달라지므로, 용어가 대표(REPRESENTS)하는 테이블로 찾는다."""
    결과 = {}
    for t in 호출("GET", "/api/terms?limit=100")["terms"]:
        for tb in 호출("GET", f"/api/exploration/terms/{t['id']}/details")["data"]["tables"]:
            if "REPRESENTS" in tb["relationship_types"]:
                결과[tb["name"]] = t
    return 결과


# 1. 용어: 테이블 → (이름, 설명)
용어_검토 = {
    "so_hdr":   ("Sales Order", "수주 헤더. 고객(cust_cd)이 언제(so_dt) 주문했는지와 상태(so_stat)를 담는다. "
                 "상태 코드는 erp.cmn_cd 의 SO_STAT 그룹에 정의되며 90 은 수주 취소다."),
    "so_dtl":   ("Sales Order Line", "수주 품목 행. 품목별 수량·단가·금액(amt)을 담으며 매출 금액의 원천이다."),
    "cust_mst": ("Customer", "고객 마스터. 완성품을 사 가는 고객사다."),
    "ship":     ("Shipment", "출하 기록. 어느 생산 로트(lot_no)를 어느 수주(so_no)로 내보냈는지 담는다."),
    "lot":      ("Production Lot", "생산 로트. 작업 지시(wo_no)로 만든 완성품 묶음이다."),
    "lot_comp": ("Lot Component", "로트 투입 내역. 생산 로트(lot_no)에 어떤 입고 로트(rcv_lot_no)의 부품이 들어갔는지 담는다."),
    "rcv_lot":  ("Receiving Lot", "부품 입고 로트. 협력사(vend_cd)에서 받은 부품 묶음과 수입 검사 결과를 담는다."),
    "insp":     ("Inspection", "출하 전 품질 검사. 생산 로트(lot_no)마다 샘플 수량(smpl_qty)과 불량 수량(dfct_qty)을 담는다."),
    "insp_dfct": ("Inspection Defect", "검사에서 나온 불량 유형별 내역. 불량 수량 합계는 insp.dfct_qty 와 같으므로 "
                  "불량률을 낼 때 insp 와 다시 곱해 세지 않는다."),
    "wo":       ("Work Order", "작업 지시. 어느 라인(line_cd)에서 어느 품목을 몇 개 만들지 담는다."),
    "wo_eq":    ("Work Order Equipment", "작업 지시별 설비 사용 기록. 어느 설비(eq_cd)를 몇 분 썼는지 담는다."),
    "line":     ("Production Line", "생산 라인. 어느 공장(plant_cd)에 속하는지 담는다."),
    "plant":    ("Plant", "공장. 구미 1공장·울산 1공장·화성 2공장이 있다."),
}

# 2. SQL 속성: (테이블, 이름, 설명, 식)
SQL_속성 = [
    ("so_hdr", "Net Revenue",
     "매출: 수주 품목 금액(so_dtl.amt) 합계. 수주 취소(so_stat = '90')는 뺀다. 주문 건수가 아니라 금액이다.",
     "SELECT h.so_no, h.cust_cd, h.so_dt, SUM(d.amt) AS net_revenue "
     "FROM factory.erp.so_hdr h JOIN factory.erp.so_dtl d ON d.so_no = h.so_no "
     "WHERE h.so_stat <> '90' GROUP BY h.so_no, h.cust_cd, h.so_dt"),
    ("insp", "Inspection Plant",
     "검사가 어느 공장에서 만든 로트에 대한 것인지: 검사 → 생산 로트 → 작업 지시 → 라인 → 공장. "
     "공장별 불량률 = SUM(dfct_qty) / SUM(smpl_qty).",
     "SELECT i.insp_no, i.smpl_qty, i.dfct_qty, p.plant_cd, p.plant_nm "
     "FROM factory.qms.insp i JOIN factory.mes.lot l ON l.lot_no = i.lot_no "
     "JOIN factory.mes.wo w ON w.wo_no = l.wo_no JOIN factory.mes.line ln ON ln.line_cd = w.line_cd "
     "JOIN factory.mes.plant p ON p.plant_cd = ln.plant_cd"),
    ("rcv_lot", "Shipped Customers",
     "리콜 역추적: 입고 로트가 투입된 생산 로트를 출하받은 고객. "
     "입고 로트 → 로트 투입 → 생산 로트 → 출하 → 수주 → 고객.",
     "SELECT lc.rcv_lot_no, s.lot_no, s.ship_no, h.cust_cd, c.cust_nm "
     "FROM factory.mes.lot_comp lc JOIN factory.erp.ship s ON s.lot_no = lc.lot_no "
     "JOIN factory.erp.so_hdr h ON h.so_no = s.so_no JOIN factory.erp.cust_mst c ON c.cust_cd = h.cust_cd"),
]

# 3. 사용자 지시문
지시문 = """이 공장 데이터베이스의 업무 규칙:
- 매출은 erp.so_dtl.amt 의 합계다. 수주 취소(erp.so_hdr.so_stat = '90')는 매출에서 뺀다. 주문 건수를 매출로 쓰지 않는다.
- 공장별 지표는 검사(qms.insp) → 생산 로트(mes.lot) → 작업 지시(mes.wo) → 라인(mes.line) → 공장(mes.plant)으로 잇는다.
- 불량률은 SUM(qms.insp.dfct_qty) / SUM(qms.insp.smpl_qty) 이다. qms.insp_dfct 와 조인하면 샘플 수량이 중복되므로 쓰지 않는다.
- 리콜 역추적은 qms.rcv_lot → mes.lot_comp → mes.lot → erp.ship → erp.so_hdr → erp.cust_mst 로 잇는다.
- 질문한 지표가 데이터에 없으면(예: 탄소 배출량, 전력 사용량) 다른 지표로 대신 계산하지 말고 데이터에 없다고 답한다."""


def main():
    용어 = 테이블별_용어()
    print(f"[용어] {len(용어)}개 테이블에 대응하는 용어를 찾았다")
    for 테이블, (이름, 설명) in 용어_검토.items():
        t = 용어.get(테이블)
        if not t:
            print(f"  {테이블}: 용어 없음, 건너뜀")
            continue
        호출("PATCH", f"/api/terms/{t['id']}", {"name": 이름, "description": 설명,
                                               "name_certified": True, "description_certified": True})
        바뀜 = "" if t["name"] == 이름 else f" (원래 '{t['name']}')"
        print(f"  {테이블:<10} → {이름}{바뀜} 인증")

    for 테이블, 이름, 설명, 식 in SQL_속성:
        t = 용어[테이블]
        기존 = {a["name"]: a for a in 호출("GET", f"/api/terms/{t['id']}/sql-attributes").get("data", [])}
        if 이름 in 기존:
            print(f"[SQL 속성] {이름}: 이미 있음")
            continue
        검증 = 호출("POST", "/api/sql-attributes/validate", {"expression": 식, "term_id": t["id"]})
        assert 검증["data"]["valid"], 검증
        새것 = 호출("POST", "/api/sql-attributes", {"name": 이름, "description": 설명,
                                                  "expression": 식, "term_id": t["id"]})
        속성_id = (새것.get("data") or 새것)["id"]
        호출("PATCH", f"/api/sql-attributes/{속성_id}", {"certified": True})
        print(f"[SQL 속성] {이름} → 용어 '{용어_검토[테이블][0]}' 에 등록·인증")

    기존_지시문 = 호출("GET", "/api/custom-prompts")
    if any(p.get("content") == 지시문 for p in 기존_지시문):
        print("[지시문] 이미 있음")
    else:
        호출("POST", "/api/custom-prompts", {"content": 지시문})
        print(f"[지시문] 업무 규칙 {지시문.count(chr(10) + '-')}줄 등록")


if __name__ == "__main__":
    main()
