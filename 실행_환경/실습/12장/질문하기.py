"""12장 실습: Auto Ontology 대화 API 에 질문을 보내고 답·SQL·단계를 결과 파일로 남긴다.

사용법:
    export AUTO_ONTOLOGY_API_TOKEN=...      # 화면 오른쪽 위 사용자 메뉴 → API Tokens 에서 발급
    python 질문하기.py 결과파일이름 "질문 1" "질문 2" ...
"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

API = os.environ.get("AUTO_ONTOLOGY_API_URL", "http://localhost:3000")
토큰 = os.environ["AUTO_ONTOLOGY_API_TOKEN"]
결과_폴더 = Path(__file__).resolve().parent.parent / "결과"


def 묻기(질문):
    요청 = urllib.request.Request(
        f"{API}/api/chat/completions",
        data=json.dumps({"question": 질문}).encode(),
        headers={"x-api-key": 토큰, "Content-Type": "application/json"},
    )
    단계, sql들, 답 = [], [], None
    시작 = time.perf_counter()
    with urllib.request.urlopen(요청, timeout=900) as 응답:
        for 줄 in 응답:
            줄 = 줄.decode().strip()
            if not 줄.startswith("data:"):
                continue
            내용 = 줄.removeprefix("data:").strip()
            if 내용 == "[DONE]":
                break
            사건 = json.loads(내용)
            if 사건["type"] == "step" and 사건.get("phase") == "end":
                단계.append({"node": 사건.get("node"), "thought": 사건.get("thought")})
            elif 사건["type"] == "sql":
                sql들.append(사건.get("sql") or 사건.get("content") or 사건)
            elif 사건["type"] == "result":
                답 = 사건["answer"]
            elif 사건["type"] == "error":
                답 = {"error": 사건.get("message")}
    return {"question": 질문, "seconds": round(time.perf_counter() - 시작, 1), "steps": 단계, "sql_events": sql들, "answer": 답}


def main():
    이름, 질문들 = sys.argv[1], sys.argv[2:]
    기록 = []
    for q in 질문들:
        print(f"\n### {q}", flush=True)
        r = 묻기(q)
        기록.append(r)
        a = r["answer"] or {}
        print(f"({r['seconds']}초)")
        print("답:", a.get("response") or a.get("error"))
        if a.get("sql_code"):
            print("SQL:\n" + a["sql_code"])
        rows = a.get("sql_response_from_db")
        if rows:
            print("행:", json.dumps(rows, ensure_ascii=False)[:800])
    (결과_폴더 / f"{이름}.json").write_text(json.dumps(기록, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(f"\n[저장] {결과_폴더 / (이름 + '.json')}")


if __name__ == "__main__":
    main()
