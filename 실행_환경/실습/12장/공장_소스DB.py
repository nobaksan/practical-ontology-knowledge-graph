"""12장 실습: Auto Ontology 가 읽을 공장 소스 DB(factory)를 만든다.

국내 제조사의 레거시 DB 를 흉내 내 테이블·컬럼 이름을 약어로 짓고(cust_mst, so_hdr, wo ...),
상태값은 숫자·문자 코드로 넣은 뒤 의미는 공통 코드 테이블(erp.cmn_cd)에만 둔다.
설명(COMMENT)은 일부러 달지 않는다. 의미를 찾아내는 일은 온톨로지 생성기의 몫이다.

사용법:
    python 공장_소스DB.py "postgresql://postgres:<비밀번호>@localhost:55433/postgres"
"""
import datetime as dt
import random
import sys

import psycopg

rnd = random.Random(2026)
관리_DSN = sys.argv[1]
시작일 = dt.date(2026, 1, 1)
결함_입고 = "RL-2026-0102"


def 날짜(최소=0, 최대=180):
    return 시작일 + dt.timedelta(days=rnd.randint(최소, 최대))


DDL = """
CREATE SCHEMA erp; CREATE SCHEMA mes; CREATE SCHEMA qms;

CREATE TABLE erp.cmn_cd (cd_grp varchar(20), cd varchar(10), cd_nm varchar(50), PRIMARY KEY (cd_grp, cd));
CREATE TABLE erp.cust_mst (cust_cd varchar(10) PRIMARY KEY, biz_no varchar(12), cust_nm varchar(50),
                           region_cd varchar(10), grade_cd char(1), reg_dt date);
CREATE TABLE erp.vend_mst (vend_cd varchar(10) PRIMARY KEY, vend_nm varchar(50), vend_tier smallint);
CREATE TABLE erp.item_mst (item_cd varchar(12) PRIMARY KEY, item_nm varchar(60), item_typ char(2),
                           uom varchar(5), std_prc numeric(14,0));
CREATE TABLE erp.so_hdr (so_no varchar(14) PRIMARY KEY, cust_cd varchar(10) REFERENCES erp.cust_mst,
                         so_dt date, req_dlv_dt date, so_stat varchar(2));
CREATE TABLE erp.so_dtl (so_no varchar(14) REFERENCES erp.so_hdr, ln_no smallint, item_cd varchar(12) REFERENCES erp.item_mst,
                         ord_qty int, unit_prc numeric(14,0), amt numeric(16,0), PRIMARY KEY (so_no, ln_no));

CREATE TABLE mes.plant (plant_cd varchar(6) PRIMARY KEY, plant_nm varchar(30), region_cd varchar(10));
CREATE TABLE mes.line (line_cd varchar(8) PRIMARY KEY, plant_cd varchar(6) REFERENCES mes.plant, line_nm varchar(30));
CREATE TABLE mes.equip (eq_cd varchar(10) PRIMARY KEY, line_cd varchar(8) REFERENCES mes.line, eq_nm varchar(40),
                        eq_typ varchar(6), inst_dt date);
CREATE TABLE mes.wo (wo_no varchar(12) PRIMARY KEY, so_no varchar(14) REFERENCES erp.so_hdr, ln_no smallint,
                     item_cd varchar(12) REFERENCES erp.item_mst, line_cd varchar(8) REFERENCES mes.line,
                     plan_qty int, good_qty int, scrap_qty int, wo_stat char(1), st_dt date, end_dt date);
CREATE TABLE mes.wo_eq (wo_no varchar(12) REFERENCES mes.wo, eq_cd varchar(10) REFERENCES mes.equip,
                        run_min int, down_min int, PRIMARY KEY (wo_no, eq_cd));
CREATE TABLE mes.lot (lot_no varchar(14) PRIMARY KEY, wo_no varchar(12) REFERENCES mes.wo, prod_qty int, prod_dt date);

CREATE TABLE qms.rcv_lot (rcv_lot_no varchar(14) PRIMARY KEY, vend_cd varchar(10) REFERENCES erp.vend_mst,
                          item_cd varchar(12) REFERENCES erp.item_mst, rcv_dt date, rcv_qty int, iqc_rslt char(1));
CREATE TABLE mes.lot_comp (lot_no varchar(14) REFERENCES mes.lot, rcv_lot_no varchar(14) REFERENCES qms.rcv_lot,
                           use_qty int, PRIMARY KEY (lot_no, rcv_lot_no));
CREATE TABLE qms.insp (insp_no varchar(14) PRIMARY KEY, lot_no varchar(14) REFERENCES mes.lot, insp_dt date,
                       smpl_qty int, dfct_qty int, rslt_cd char(1));
CREATE TABLE qms.insp_dfct (insp_no varchar(14) REFERENCES qms.insp, dfct_cd varchar(6), dfct_qty int,
                            PRIMARY KEY (insp_no, dfct_cd));
CREATE TABLE erp.ship (ship_no varchar(14), lot_no varchar(14) REFERENCES mes.lot, so_no varchar(14) REFERENCES erp.so_hdr,
                       ship_dt date, ship_qty int, PRIMARY KEY (ship_no, lot_no));
"""

공통코드 = [
    ("SO_STAT", "10", "수주 접수"), ("SO_STAT", "20", "생산 중"), ("SO_STAT", "30", "출하 완료"), ("SO_STAT", "90", "수주 취소"),
    ("WO_STAT", "R", "작업 대기"), ("WO_STAT", "S", "작업 중"), ("WO_STAT", "C", "작업 완료"),
    ("RSLT_CD", "P", "합격"), ("RSLT_CD", "F", "불합격"), ("RSLT_CD", "H", "판정 보류"),
    ("ITEM_TYP", "FG", "완제품"), ("ITEM_TYP", "SA", "반제품"), ("ITEM_TYP", "RM", "원자재·구매 부품"),
    ("GRADE_CD", "A", "핵심 고객"), ("GRADE_CD", "B", "일반 고객"), ("GRADE_CD", "C", "신규 고객"),
    ("DFCT_CD", "D01", "치수 불량"), ("DFCT_CD", "D02", "표면 긁힘"), ("DFCT_CD", "D03", "용접 기공"),
    ("DFCT_CD", "D04", "센서 오작동"), ("DFCT_CD", "D05", "도장 박리"),
    ("REGION", "US", "울산"), ("REGION", "HS", "화성"), ("REGION", "GM", "구미"), ("REGION", "SE", "서울"),
    ("REGION", "CW", "창원"), ("REGION", "CJ", "청주"),
]

공장 = [("ULS1", "울산 1공장", "US"), ("HWS2", "화성 2공장", "HS"), ("GUM1", "구미 1공장", "GM")]
라인 = [("ULS1-L1", "ULS1", "프레스 라인"), ("ULS1-L2", "ULS1", "용접 라인"), ("ULS1-L3", "ULS1", "조립 라인"),
        ("HWS2-L1", "HWS2", "가공 라인"), ("HWS2-L2", "HWS2", "조립 라인"),
        ("GUM1-L1", "GUM1", "레이저 라인"), ("GUM1-L2", "GUM1", "조립 라인")]
설비유형 = {"프레스 라인": "PRESS", "용접 라인": "WELD", "조립 라인": "ASSY", "가공 라인": "CNC", "레이저 라인": "LASER"}

완제품 = [("FG-1001", "EV 배터리팩 케이스", 2_400_000), ("FG-1002", "차량용 알루미늄 샤시", 1_850_000),
          ("FG-1003", "서버용 방열 모듈", 920_000), ("FG-1004", "원통형 배터리 캔", 18_000),
          ("FG-1005", "모터 하우징", 640_000), ("FG-1006", "인버터 브래킷", 85_000)]
부품 = [("P-10482", "온도 센서 칩", 4_200), ("P-10483", "압력 센서 칩", 5_100), ("P-20110", "알루미늄 판재", 38_000),
        ("P-20111", "구리 방열판", 21_000), ("P-30007", "고정 볼트 세트", 1_200), ("P-30008", "실링 가스켓", 2_300)]
협력사 = [("V001", "대성반도체", 2), ("V002", "한결소재", 1), ("V003", "누리정밀", 2), ("V004", "바른화학", 1)]
부품_협력사 = {"P-10482": "V001", "P-10483": "V001", "P-20110": "V002", "P-20111": "V002", "P-30007": "V003", "P-30008": "V004"}
제품_부품 = {"FG-1001": ["P-10482", "P-20110", "P-30007"], "FG-1002": ["P-20110", "P-30007"],
            "FG-1003": ["P-10482", "P-20111", "P-30008"], "FG-1004": ["P-20110"],
            "FG-1005": ["P-10483", "P-20110", "P-30008"], "FG-1006": ["P-30007"]}
고객명 = ["한빛모터스", "누리전자", "바른에너지", "다온오토", "미래셀", "가람테크", "세움자동차", "온새미로지스",
          "하늘배터리", "새솔전기", "도담기계", "라온시스템", "나래모빌리티", "보람파워", "슬기산업", "아름정공",
          "푸른전장", "한결오토", "해솔에너지", "가온정밀"]


def main():
    with psycopg.connect(관리_DSN, autocommit=True) as c:
        c.execute("DROP DATABASE IF EXISTS factory")
        c.execute("CREATE DATABASE factory")
    dsn = 관리_DSN.rsplit("/", 1)[0] + "/factory"
    with psycopg.connect(dsn) as c, c.cursor() as cur:
        cur.execute(DDL)
        cur.executemany("INSERT INTO erp.cmn_cd VALUES (%s,%s,%s)", 공통코드)
        고객 = []
        for i, nm in enumerate(고객명):
            고객.append((f"C{i + 1:04d}", f"{rnd.randint(100, 899)}-{rnd.randint(10, 99)}-{rnd.randint(10000, 99999)}",
                         nm, rnd.choice(["US", "HS", "GM", "SE", "CW", "CJ"]), rnd.choice("AABBC"), 날짜(-900, -30)))
        cur.executemany("INSERT INTO erp.cust_mst VALUES (%s,%s,%s,%s,%s,%s)", 고객)
        cur.executemany("INSERT INTO erp.vend_mst VALUES (%s,%s,%s)", 협력사)
        cur.executemany("INSERT INTO erp.item_mst VALUES (%s,%s,'FG','EA',%s)", 완제품)
        cur.executemany("INSERT INTO erp.item_mst VALUES (%s,%s,'RM','EA',%s)", 부품)
        cur.executemany("INSERT INTO mes.plant VALUES (%s,%s,%s)", 공장)
        cur.executemany("INSERT INTO mes.line VALUES (%s,%s,%s)", 라인)
        설비 = []
        for lc, pc, ln in 라인:
            for k in range(1, rnd.randint(3, 6)):
                설비.append((f"{설비유형[ln][:3]}-{pc[:1]}{lc[-1]}{k:02d}", lc, f"{ln.split()[0]} {k}호기", 설비유형[ln], 날짜(-2000, -100)))
        cur.executemany("INSERT INTO mes.equip VALUES (%s,%s,%s,%s,%s)", 설비)

        # 협력사 입고 로트. P-10482 의 세 번째 로트(RL-2026-0102)는 입고 검사는 통과했지만 나중에 결함이 드러난다.
        입고 = []
        for 부품코드, _, _ in 부품:
            for j in range(12):
                no = f"RL-2026-{len(입고) + 100:04d}"
                입고.append((no, 부품_협력사[부품코드], 부품코드, 날짜(j * 15, j * 15 + 10), rnd.randint(5, 20) * 1000,
                             "P" if rnd.random() > 0.05 or no == 결함_입고 else "F"))
        cur.executemany("INSERT INTO qms.rcv_lot VALUES (%s,%s,%s,%s,%s,%s)", 입고)
        입고_부품별 = {}
        for r in 입고:
            if r[5] == "P":
                입고_부품별.setdefault(r[2], []).append(r)

        수주, 수주상세, 작업, 작업설비, 로트, 로트부품, 검사, 검사불량, 출하 = [], [], [], [], [], [], [], [], []
        조립라인 = {p: [l for l in 라인 if l[1] == p] for p, _, _ in 공장}
        for i in range(1, 801):
            so_no = f"SO2026{i:06d}"
            cust = rnd.choice(고객)
            so_dt = 날짜(0, 170)
            stat = rnd.choices(["10", "20", "30", "90"], [5, 15, 72, 8])[0]
            수주.append((so_no, cust[0], so_dt, so_dt + dt.timedelta(days=rnd.randint(14, 45)), stat))
            for ln in range(1, rnd.randint(2, 4)):
                item = rnd.choice(완제품)
                qty = rnd.randint(1, 40) * (50 if item[2] < 100_000 else 2)
                prc = round(item[2] * rnd.uniform(0.92, 1.05), -2)
                수주상세.append((so_no, ln, item[0], qty, prc, qty * prc))
                if stat in ("10", "90"):
                    continue
                plant = rnd.choice(공장)[0]
                line = rnd.choice(조립라인[plant])
                wo_no = f"WO{len(작업) + 1:07d}"
                st = so_dt + dt.timedelta(days=rnd.randint(1, 5))
                scrap = int(qty * rnd.uniform(0, 0.06 if plant != "GUM1" else 0.11))
                done = stat == "30"
                작업.append((wo_no, so_no, ln, item[0], line[0], qty, qty - scrap if done else 0, scrap if done else 0,
                             "C" if done else "S", st, st + dt.timedelta(days=rnd.randint(2, 9)) if done else None))
                for eq in rnd.sample([e for e in 설비 if e[1] == line[0]], k=min(2, len([e for e in 설비 if e[1] == line[0]]))):
                    run = rnd.randint(300, 3000)
                    작업설비.append((wo_no, eq[0], run, int(run * rnd.uniform(0, 0.15))))
                if not done:
                    continue
                lot_no = f"LT{len(로트) + 1:08d}"
                로트.append((lot_no, wo_no, qty - scrap, 작업[-1][10]))
                for 부품코드 in 제품_부품[item[0]]:
                    후보 = [r for r in 입고_부품별[부품코드] if r[3] <= st] or 입고_부품별[부품코드][:1]
                    로트부품.append((lot_no, 후보[-1 if rnd.random() < 0.7 else max(-len(후보), -2)][0], qty))
                smpl = min(qty, rnd.choice([5, 8, 13, 20, 32]))
                결함로트 = any(lc[0] == lot_no and lc[1] == 결함_입고 for lc in 로트부품[-3:])
                dfct = rnd.choices([0, 1, 2], [85, 12, 3])[0] + (rnd.randint(2, 4) if 결함로트 else 0)
                dfct = min(dfct, smpl)
                insp_no = f"IN{len(검사) + 1:08d}"
                검사.append((insp_no, lot_no, 작업[-1][10], smpl, dfct, "P" if dfct <= 1 else ("H" if dfct == 2 else "F")))
                if dfct:
                    코드 = "D04" if 결함로트 else rnd.choice(["D01", "D02", "D03", "D05"])
                    검사불량.append((insp_no, 코드, dfct))
                출하.append((f"SH{len(출하) + 1:08d}", lot_no, so_no, 작업[-1][10] + dt.timedelta(days=rnd.randint(1, 4)), qty - scrap))

        for 표, 행, n in [("erp.so_hdr", 수주, 5), ("erp.so_dtl", 수주상세, 6), ("mes.wo", 작업, 11), ("mes.wo_eq", 작업설비, 4),
                          ("mes.lot", 로트, 4), ("mes.lot_comp", 로트부품, 3), ("qms.insp", 검사, 6),
                          ("qms.insp_dfct", 검사불량, 3), ("erp.ship", 출하, 5)]:
            cur.executemany(f"INSERT INTO {표} VALUES ({','.join(['%s'] * n)})", 행)
        c.commit()
        cur.execute("ANALYZE")
        for 표 in ["erp.cmn_cd", "erp.cust_mst", "erp.vend_mst", "erp.item_mst", "erp.so_hdr", "erp.so_dtl", "erp.ship",
                   "mes.plant", "mes.line", "mes.equip", "mes.wo", "mes.wo_eq", "mes.lot", "mes.lot_comp",
                   "qms.rcv_lot", "qms.insp", "qms.insp_dfct"]:
            cur.execute(f"SELECT count(*) FROM {표}")
            print(f"{표:<16} {cur.fetchone()[0]:>6,}행")


if __name__ == "__main__":
    main()
