# 12장_Auto_Ontology_온톨로지_자동_생성과_사람_검토_실습

본문에 실린 순서대로 코드 블록 13개를 그대로 옮겼다.

| 파일 | 절 | 언어 | 첫 줄 |
|---|---|---|---|
| [01.sh](01.sh) | 2.1 주석 없는 3개 스키마, 17개 테이블의 레거시 설계 | bash | `python 실행_환경/실습/12장/공장_소스DB.py "postgresql://postgres:<비밀번호>` |
| [02.sh](02.sh) | 3.1 1차 질의: 10~27분 지연과 응답 실패의 원인 | bash | `export AUTO_ONTOLOGY_API_TOKEN=...   # 화면 오른쪽 위 사용자 메뉴 → API` |
| [03.sh](03.sh) | 3.2 `llm_invoke.py` 패치와 2차 질의: 속도와 의미의 분리 | bash | `REASONING_MODEL_KWARGS='{"chat_template_kwargs": {"enable_th` |
| [04.sh](04.sh) | 4.1 컴파일마다 달라지는 용어 목록과 환각 용어 | bash | `python 실행_환경/실습/12장/관계_스냅숏.py 12장_온톨로지_패치후` |
| [05.sql](05.sql) | 5.1 3차 질의 결과와 지표·조인 오류 해부 | sql | `SELECT c.cust_nm, COUNT(s.so_no) AS total_sales` |
| [06.sql](06.sql) | 5.1 3차 질의 결과와 지표·조인 오류 해부 | sql | `SELECT CAST(SUM(d.dfct_qty) AS REAL) / SUM(i.smpl_qty) * 100` |
| [07.sql](07.sql) | 5.2 리콜 역추적 0행의 함정과 대리 지표 문제 | sql | `SELECT DISTINCT c.cust_cd` |
| [08.sql](08.sql) | 5.2 리콜 역추적 0행의 함정과 대리 지표 문제 | sql | `SELECT c.cust_nm, COUNT(DISTINCT s.lot_no) AS 출하_로트` |
| [09.sh](09.sh) | 6.1 업무 언어로 용어 바로잡기와 인증 배지 | bash | `python 실행_환경/실습/12장/사람_검토.py` |
| [10.sql](10.sql) | 6.2 SQL 속성 검증·등록과 탐색 그래프 확인 | sql | `SELECT h.so_no, h.cust_cd, h.so_dt, SUM(d.amt) AS net_revenu` |
| [11.txt](11.txt) | 6.3 사용자 지시문 등록과 규칙 근거 검토의 중요성 | text | `이 공장 데이터베이스의 업무 규칙:` |
| [12.sql](12.sql) | 7.1 4차 질의 채점: 매출, 불량률, 탄소 배출량의 교정 | sql | `SELECT c.cust_nm AS customer_name, SUM(d.amt) AS total_sales` |
| [13.sql](13.sql) | 7.1 4차 질의 채점: 매출, 불량률, 탄소 배출량의 교정 | sql | `SELECT p.plant_cd, p.plant_nm,` |
