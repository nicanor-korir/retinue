-- Check which agents exist in the database
SELECT agent_id, name, role, status
FROM agents
ORDER BY agent_id;

-- If hr_monitor_001 doesn't exist, you can add it with:
-- INSERT INTO agents (agent_id, name, role, llm_model, system_prompt, agent_type, status)
-- VALUES (
--     'hr_monitor_001',
--     'HR Monitor',
--     'HR',
--     'claude-sonnet-4-20250514',
--     'You are an HR monitoring assistant. Help with HR-related questions and tasks.',
--     'SPECIALIST',
--     'AVAILABLE'
-- );

-- Or check if you meant to use a different agent:
-- Common agent IDs:
-- - ceo_001
-- - cto_001
-- - pm_001
-- - frontend_001
-- - backend_001
-- - designer_001
