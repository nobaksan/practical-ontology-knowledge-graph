"""실습 스크립트가 함께 쓰는 접속 정보와 측정 도구."""
import os
import platform
import statistics
import subprocess
import time
from pathlib import Path

PG_DSN = os.environ.get(
    "ONTO_PG_DSN", "postgresql://onto:Ontology2026!@localhost:55432/factory"
)
NEO4J_URI = os.environ.get("ONTO_NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = ("neo4j", os.environ.get("ONTO_NEO4J_PASSWORD", "Ontology2026!"))

결과_폴더 = Path(__file__).resolve().parent / "결과"
결과_폴더.mkdir(exist_ok=True)


def 측정(함수, 반복=30, 예열=5):
    """함수를 예열한 뒤 반복 실행해 중앙값과 95번째 백분위(ms)를 돌려준다."""
    for _ in range(예열):
        함수()
    기록 = []
    for _ in range(반복):
        시작 = time.perf_counter()
        함수()
        기록.append((time.perf_counter() - 시작) * 1000)
    기록.sort()
    return statistics.median(기록), 기록[int(len(기록) * 0.95) - 1]


def 실행_환경_설명():
    try:
        cpu = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        cpu = platform.processor()
    return f"{cpu} · {platform.system()} {platform.release()} · Python {platform.python_version()}"


class 기록기:
    """화면에 찍으면서 같은 내용을 결과 파일에도 남긴다."""

    def __init__(self, 이름):
        self.경로 = 결과_폴더 / 이름
        self.줄 = []

    def __call__(self, *값):
        줄 = " ".join(str(v) for v in 값)
        print(줄, flush=True)
        self.줄.append(줄)

    def 저장(self):
        self.경로.write_text("\n".join(self.줄) + "\n", encoding="utf-8")
        print(f"\n[저장] {self.경로}")
