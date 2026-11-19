# 시맨틱 CI/CD 파이프라인의 사전 검증 실행 예시
$ metrics validate --all
✓ 파싱 완료: 총 14개 시맨틱 모델 구문 검증 통과
✓ 참조 무결성 검증: 모든 measure 컬럼이 물리 스키마에 실존함을 확인

$ metrics diff --against main
[변경 감지] monthly_active_users:
  - 필터 변경: 'is_internal_account = FALSE' 조건 추가됨
  ! 영향도 시뮬레이션: 2026년 08월 지표 수치가 12,450명 -> 10,240명으로 변동 (-17.7%)
  ! 승인 필요: 소유자(growth_team) 및 재무 승인권자(finance_lead)의 서명이 요구됨
