-- [대시보드 A] 마케팅팀 운영 대시보드
-- 단순 로그인 트래픽 기반 카운트
SELECT COUNT(DISTINCT user_id) AS active_users
FROM event_logs
WHERE event_name = 'login'
  AND event_time >= '2026-08-01' 
  AND event_time < '2026-09-01';

-- [대시보드 B] 제품 및 경영진 보고용 대시보드
-- 실제 가치 창출 액션(생성, 댓글, 공유) 수행 및 내부 테스트 계정 제외
SELECT COUNT(DISTINCT user_id) AS active_users
FROM event_logs
WHERE event_name IN ('create_post', 'write_comment', 'share_content')
  AND event_time >= '2026-08-01' 
  AND event_time < '2026-09-01'
  AND user_id NOT IN (SELECT user_id FROM internal_test_accounts);
