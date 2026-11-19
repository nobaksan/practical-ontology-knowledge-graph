"""12장 실습: 생성된 온톨로지의 용어·관계를 결과 파일로 떠 둔다.

용어 이름은 컴파일할 때마다 달라질 수 있으므로, 테이블 이름으로 용어를 찾는다.
사용법: python 관계_스냅숏.py <결과이름>
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

API = os.environ.get("AUTO_ONTOLOGY_API_URL", "http://localhost:3000")
H = {"x-api-key": os.environ["AUTO_ONTOLOGY_API_TOKEN"]}
결과_폴더 = Path(__file__).resolve().parent.parent / "결과"

# 리콜 역추적: 입고 로트 → 로트 투입 → 생산 로트 → 출하 → 수주 → 고객
# 공장별 불량률: 검사 → 생산 로트 → 작업 지시 → 라인 → 공장
경로 = [("rcv_lot", "lot_comp"), ("lot_comp", "lot"), ("lot", "ship"), ("ship", "so_hdr"),
        ("so_hdr", "cust_mst"), ("rcv_lot", "cust_mst"),
        ("insp", "lot"), ("lot", "wo"), ("wo", "line"), ("line", "plant"), ("insp", "plant")]


def get(p):
    return json.load(urllib.request.urlopen(urllib.request.Request(API + p, headers=H)))


def main():
    이름 = sys.argv[1]
    용어 = get("/api/terms?limit=100")["terms"]
    테이블_용어 = {}
    줄 = [f"# 테이블 → 생성된 용어 ({len(용어)}개)"]
    for t in 용어:
        for tb in get(f"/api/exploration/terms/{t['id']}/details")["data"]["tables"]:
            if "REPRESENTS" in tb["relationship_types"]:  # HAS_ATTRIBUTE 만 있는 테이블은 빌려 온 열이다
                테이블_용어[tb["name"]] = t
    for 테이블 in sorted(테이블_용어):
        t = 테이블_용어[테이블]
        줄.append(f"- {테이블:<10} {t['name']}: {(t.get('description') or '(설명 없음)')[:70]}")
    줄.append("\n# 용어 사이 의미 경로")
    for a, b in 경로:
        if a not in 테이블_용어 or b not in 테이블_용어:
            줄.append(f"{a} → {b}: 용어 없음")
            continue
        홉 = get(f"/api/exploration/terms/{테이블_용어[a]['id']}/path/{테이블_용어[b]['id']}")["data"]["hops"]
        fk = [f"{h['source']['name']}→{h['target']['name']}" for h in 홉 if h["relationship"] == "SEMANTIC_FK"]
        줄.append(f"{a} → {b}: " + (f"{len(홉)}홉, FK " + ", ".join(fk) if 홉 else "경로 없음"))
    텍스트 = "\n".join(줄)
    print(텍스트)
    (결과_폴더 / f"{이름}.txt").write_text(텍스트 + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
