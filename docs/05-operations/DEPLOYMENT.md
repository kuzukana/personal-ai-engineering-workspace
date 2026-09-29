# Personal AI Engineering Workspace — Deployment Specification

**Version:** 0.1  
**Status:** Draft  
**Last Updated:** 2026-09-29

# 1. Purpose

定义本地开发、Docker Compose、环境配置、数据库迁移、CI/CD 和未来远程部署策略。

# 2. MVP Topology

Browser → Next.js → FastAPI → PostgreSQL / Redis；FastAPI 再访问 LLM Providers、Search、GitHub。

# 3. Local Development

允许 frontend 和 backend 独立开发启动；PostgreSQL/Redis 优先由 Docker Compose 提供。

# 4. Containers

V0.1 目标服务：frontend、backend、postgres、redis。每个服务使用独立 Dockerfile 或官方镜像。

# 5. Environment Configuration

通过环境变量配置 APP_ENV、DATABASE_URL、REDIS_URL、FRONTEND_ORIGIN、Provider API Keys。真实 Secret 仅存在本地 .env 或部署平台 Secret Store。

# 6. Database Migration

使用 Alembic。部署顺序：backup/verify → migration → application rollout → health verification。禁止手工漂移 Schema。

# 7. Health

/health 检测进程；/ready 检测数据库/Redis。容器 healthcheck 依赖这些端点。

# 8. Redis

V0.1 用于短期 runtime/event communication 与缓存方向。Redis 数据不作为长期业务事实来源。

# 9. Persistent Storage

PostgreSQL 使用持久 volume。开发环境可重建，正式数据环境必须备份。

# 10. Networking

PostgreSQL、Redis 默认仅内部网络可访问；仅 frontend/backend 必要端口映射到宿主机。

# 11. CI/CD

main push / PR 运行 lint、typecheck、tests、build。真实 Provider smoke tests 手动或定时执行。通过后才视为可部署版本。

# 12. Build Artifacts

Frontend 生成生产 build；Backend 使用固定依赖安装。镜像应可重复构建并记录 Git commit SHA。

# 13. Version Metadata

服务启动时可暴露非敏感 build metadata：app version、git SHA、build timestamp。

# 14. Rollback

应用代码回滚与数据库回滚分开设计。破坏性 migration 必须采用 expand/migrate/contract 思路，不假定简单 downgrade 永远安全。

# 15. Backups

远程部署前必须有 PostgreSQL backup + restore 验证。仅“有备份文件”不等于恢复能力。

# 16. Secrets

生产 Secret 使用部署平台 secret mechanism，不 bake 进镜像、不写 Git、不打印日志。

# 17. Environments

建议：local、test、future staging、future production。不同环境使用独立数据库和 Secret。

# 18. Resource Limits

Future 为 backend、worker、database 设置 CPU/memory limits。Agent Run 还需 token/cost/step budget。

# 19. Background Workers

V0.1 可先使用应用内 background execution；当长任务和并发增长后迁移至 queue + worker，不改变 Run API 契约。

# 20. Remote Deployment

远程部署前补齐 authentication、TLS、CORS、secret store、backup、monitoring、retention 和 rate limiting。

# 21. MVP Acceptance Criteria

1. Docker Compose 可启动核心依赖；2. Backend 可连 PostgreSQL/Redis；3. Alembic 可从空库升级；4. /health /ready 可用于 healthcheck；5. Secret 不进镜像和 Git；6. CI 可阻止明显错误；7. 代码版本可追踪到 commit；8. 数据 volume 独立；9. remote deployment 前置安全项明确；10. 架构允许未来 worker 化。

# 22. Final Principle

> **Deployment should reproduce the same contracts across environments while keeping secrets, data and runtime state explicitly separated.**
