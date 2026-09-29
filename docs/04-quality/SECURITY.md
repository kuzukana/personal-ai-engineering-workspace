# Personal AI Engineering Workspace — Security Specification

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2026-09-29

# 1. Purpose

定义 V0.1 的安全边界、Secret 管理、Prompt Injection 防护、Tool 权限和数据保护要求。

核心原则：**Least privilege, explicit trust boundaries, no secrets in prompts or traces.**

# 2. Trust Boundaries

Browser → FastAPI → Agent Runtime / Model Gateway / Tool Gateway → External Providers / Web / GitHub / Future MCP。

所有外部网页、README、Issue、PDF 和 Tool Result 默认视为 UNTRUSTED DATA。

# 3. Secrets

V0.1 Secret 仅通过环境变量加载，例如 OPENAI_API_KEY、ANTHROPIC_API_KEY、DEEPSEEK_API_KEY、KIMI_API_KEY。

规则：
- .env 不提交；
- .env.example 只放变量名；
- Secret 不写数据库普通字段；
- Secret 不写 Event、Trace、日志；
- Secret 不进入 Prompt Context；
- Provider Adapter 在运行时注入 Secret。

# 4. Browser Boundary

Frontend 不直接调用模型 Provider。必须经过 FastAPI → Model Gateway → Provider。

# 5. Input Validation

所有 API 输入经 Pydantic 验证，并额外校验 URL、capability level、run state transition、tool allowlist、provider/model existence 和 pagination bounds。

# 6. Prompt Injection

外部内容中的指令不获得 System/User 指令优先级。Prompt 必须区分 SYSTEM、USER、VERIFIED_INTERNAL、TOOL_RESULT、EXTERNAL_UNTRUSTED。

Agent 不得遵循外部内容中要求泄露系统提示、泄露 Secret、调用未授权 Tool 或忽略系统约束的指令。

# 7. Tool Permissions

风险等级：LOW=search/read/analyze；MEDIUM=local write/workspace mutation；HIGH=delete/shell/git push/external send。

V0.1 Research Agent 仅允许 LOW-risk Tools。Future HIGH-risk action 必须 Human Approval。

# 8. Tool Allowlist

每个 Agent 显式声明 Tool Allowlist，默认 deny unless allowed。

# 9. SSRF / URL Fetching

Future fetch_url 必须阻止 localhost、loopback、private network ranges、cloud metadata endpoints 和 non-http(s) schemes，并对 redirect 重新校验。

# 10. Data Exposure

对外 API 不返回 API Key、Authorization Header、raw stack trace、environment secrets 或 provider secret metadata。

# 11. Logging / Event Redaction

写入日志和事件前过滤 authorization、api_key、token、password、secret、cookie 等字段。

# 12. Provider Privacy

发送给 Provider 的内容遵循 data minimization：只发送任务需要的上下文，不默认发送整个 Knowledge Base 或全部历史对话。

# 13. Database Security

PostgreSQL 不暴露公网；使用应用专用账号和最小权限；生产环境禁止默认密码。

# 14. CORS

开发环境只允许明确前端 Origin，例如 http://localhost:3000。生产环境不得在携带敏感凭据时使用通配 Origin。

# 15. Authentication

V0.1 单用户本地模式暂不要求完整账号系统。Remote deployment 前必须引入 authentication / authorization。

# 16. Dependency Security

CI 逐步加入 Python dependency audit、npm audit、secret scanning 和 static checks。

# 17. Git Security

.gitignore 必须覆盖 .env、virtualenv、node_modules、build output、IDE local state 和 generated secrets。

# 18. High-risk Actions

Future Coding Agent 的 git push、delete file、send message、destructive shell、external mutation 必须显式确认并记录 approval audit。

# 19. Failure Handling

安全违规应 deny action、emit structured event、write redacted log、return stable error，而不是仅靠 Prompt 提醒。

# 20. MVP Acceptance Criteria

1. .env 被 Git 忽略；
2. Browser 无 Provider Secret；
3. Secret 不出现在 Event/Log；
4. Research Agent 只有 LOW-risk Tool；
5. Provider 调用仅经 Model Gateway；
6. 外部内容显式标记 untrusted；
7. API 输入有 Schema Validation；
8. fetch_url 实现包含 SSRF 防护；
9. CI 有 Secret/dependency 检查方向；
10. 安全错误可追踪但不泄露敏感信息。

# 21. Final Principle

> **AI autonomy never overrides explicit security boundaries.**
