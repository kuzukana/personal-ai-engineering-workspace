# Personal AI Engineering Workspace — Observability Specification

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2026-09-29

# 1. Purpose

定义传统 Web 服务与 AI/Agent Runtime 的可观测性规范，回答 What happened、Where、How long、How much、Why failed。

# 2. Signals

V0.1 使用 Logs、Metrics、Domain Events；Future 增加 OpenTelemetry Traces。

# 3. Correlation

所有 Agent Run 相关记录尽可能携带 run_id。Future 增加 trace_id、span_id、request_id。

# 4. Structured Logging

建议字段：timestamp、level、service、event、request_id、run_id、agent_id、model、tool、message。

# 5. Log Levels

DEBUG 用于开发诊断；INFO 用于正常生命周期；WARNING 用于可恢复异常；ERROR 用于操作失败；CRITICAL 用于服务级故障。

# 6. Secret Redaction

日志不得包含 API Key、Token、Password、Cookie、Authorization Header。

# 7. HTTP Metrics

记录 request_count、request_latency、response_status、error_rate。Future 聚合 P50/P95/P99。

# 8. AI Metrics

每次模型调用记录 provider、model、latency_ms、ttft_ms、input_tokens、output_tokens、reasoning_tokens、estimated_cost、finish_reason、success。

# 9. Agent Metrics

每个 Run 记录 run_status、total_latency、step_count、tool_call_count、tool_failure_count、model_call_count、token_total、estimated_cost、evaluation_status。

# 10. Tool Metrics

记录 tool_name、status、latency、retry_count、error_code。

# 11. Evaluation Metrics

记录 evaluator、metric_name、status、score、latency。

# 12. Events vs Logs

Event 描述领域事实，例如 tool.failed；Log 描述实现诊断，例如 connection pool exhausted。

# 13. Run Timeline

Agent Lab 必须可根据 EVENT_SPEC 重建 Run、Agent Steps、Model Calls、Tool Calls、Evaluation 和 Failure。

# 14. Error Taxonomy

至少按 VALIDATION_ERROR、PROVIDER_ERROR、MODEL_ERROR、TOOL_ERROR、WORKFLOW_ERROR、DATABASE_ERROR、PERMISSION_ERROR、UNKNOWN_ERROR 聚合。

# 15. Cost Observability

Cost 为估算值时必须标记 estimated。Future 可按 run、model、provider、day 聚合。

# 16. Performance Baseline

V0.1 先建立 baseline，不提前承诺生产 SLA。重点观察 API latency、Time To First Event、TTFT、Total Run Latency、Tool Latency。

# 17. Health Checks

/health 表示进程存活；/ready 表示数据库/Redis 等核心依赖可用。单一 Provider 故障不应让整个 API readiness 失败。

# 18. OpenTelemetry Direction

Future 使用 OpenTelemetry 对接 FastAPI、Model Call、Tool Call、PostgreSQL、Redis；Domain Event 仍保留。

# 19. Retention

V0.1 日志合理轮转；持久化 Run Event 长期保留；token delta 不默认长期落库。

# 20. Dashboards

Future 展示 Run Success Rate、Provider Error Rate、Tool Failure Rate、Latency、Tokens、Estimated Cost、Evaluation Pass Rate。

# 21. Alerts

Future remote deployment 对 service down、database unavailable、error-rate spike、provider-wide failure、cost anomaly 告警。

# 22. MVP Acceptance Criteria

1. 日志结构化；2. Run 可通过 run_id 串联；3. Provider/Model/Tool latency 可记录；4. Token 与 Cost 可记录；5. Error 有稳定分类；6. Timeline 可由 Event 重建；7. Secret 被 Redact；8. /health 与 /ready 可测试；9. Observability 不依赖前端；10. Future 可平滑接 OTel。

# 23. Final Principle

> **Observability explains AI behavior with evidence, not guesses.**
