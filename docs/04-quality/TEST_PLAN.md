# Personal AI Engineering Workspace — Test Plan

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2026-09-29

# 1. Purpose

定义 V0.1 自动测试、集成测试、AI Contract Test、回归测试与 CI 质量门槛。

# 2. Test Layers

Unit → Contract → Integration → API → Agent Workflow → Real-provider Smoke。

LLM Judge 不能替代普通单元测试。

# 3. Backend Unit Tests

覆盖 settings、error normalization、schema validation、provider capability checking、event envelope、evaluation rules、repository/service logic。

# 4. Frontend Tests

覆盖 event reducer、API client、status rendering、model selector 和基础组件逻辑。

# 5. Provider Contract Tests

所有 Provider Adapter 验证 generate、stream、usage、error normalization、structured output，以及支持时的 tool call。

普通 CI 使用 MockProvider，不消耗真实 API。

# 6. MockProvider

必须支持 fixed text、streamed chunks、scripted tool call、usage、timeout、rate-limit、invalid structured output。

# 7. Tool Contract Tests

验证 input/output schema、timeout、error normalization、risk level、redaction。

# 8. Event Tests

验证 required fields、sequence monotonicity、serialization、SSE format、unknown event tolerance、secret redaction。

# 9. API Tests

至少覆盖 /health、/ready、/api/v1/models、POST /api/v1/research、GET run、event history、evaluations。

# 10. Database Tests

验证 Alembic from empty DB、FK、unique constraints、capability level、run event ordering、AgentVersion history。

# 11. Research Workflow Tests

使用 MockProvider + MockTools 覆盖 happy path、search failure、fetch failure、provider timeout、rate limit、invalid structured output、cancelled run、insufficient source。

# 12. Evaluation Tests

DeterministicEvaluator 对固定输入必须可重复，覆盖 valid report、missing title、missing source、invalid URL、evaluator failure。

# 13. Security Tests

验证 .env ignored、secrets redacted、unsupported tool denied、invalid URL rejected、provider secret 不出 API response。

# 14. Regression Set

从真实使用中逐步积累 technical comparison、GitHub research、current-info、conflicting sources、tool failure、structured output failure。

# 15. Real Provider Smoke Tests

不在每次 CI 默认运行；手动/定时执行小额真实调用并使用 GitHub Actions Secrets。

# 16. Frontend Integration

验证 create research request、receive mocked SSE、timeline updates、final output render、error state。

# 17. E2E MVP Flow

open app → choose model → submit research → receive progress → view report → save knowledge → inspect run。

# 18. CI Gates

逐步启用 backend lint/type/tests、frontend lint/typecheck/tests/build、secret scan、dependency checks。

# 19. Determinism

普通测试不得依赖真实 LLM 输出。使用 MockProvider、MockTool 和固定时钟。

# 20. Flaky Test Rule

非确定性 Benchmark 与 deterministic CI 分离，不接受“AI 天然 flaky”作为普通 CI 不稳定理由。

# 21. Coverage

V0.1 不追求虚假高覆盖率，优先覆盖 contracts、state transitions、security boundaries、adapters 和 evaluation。

# 22. Test Data

测试数据不得包含真实 Secret 或敏感个人信息。

# 23. CI Failure Artifacts

保留 failing test、concise logs、test report；Future E2E 增加 screenshots/traces。

# 24. MVP Acceptance Criteria

1. Backend tests 可单命令运行；2. Frontend checks 可单命令运行；3. MockProvider 使 CI 不依赖真实 LLM；4. Event/API contracts 有测试；5. DB migration 可测试；6. Research workflow 有成功/失败 case；7. Secret 不进入 fixture/log；8. main push 自动 CI；9. Real-provider smoke 与普通 CI 分离；10. 测试失败阻止错误版本被视为可交付。

# 25. Final Principle

> **Make deterministic engineering deterministic; isolate AI nondeterminism instead of letting it infect the test suite.**
