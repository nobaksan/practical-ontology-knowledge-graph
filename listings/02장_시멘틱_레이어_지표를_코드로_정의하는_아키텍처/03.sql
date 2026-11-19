-- 시맨틱 컴파일러가 기계적으로 생성한 실행 SQL
SELECT
  user_plan_tier AS plan,
  COUNT(DISTINCT user_id) AS monthly_active_users
FROM analytics.fct_events
WHERE event_name IN ('create_post', 'write_comment', 'share_content')
  AND is_internal_account = FALSE
  AND CAST(event_timestamp AS DATE) >= '2026-08-01'
  AND CAST(event_timestamp AS DATE) < '2026-09-01'
GROUP BY user_plan_tier;
