# 变更记录

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 新增

- **Web UI（FastAPI + SSE）**
  - 全新浏览器图形界面，突破命令行用户圈层
  - 左侧对话历史（支持 Markdown 渲染），右侧角色状态与快捷操作面板
  - 流式 SSE 响应，模拟打字机效果展示智能体回复
  - 世界观构建改为分步表单，适配浏览器交互
  - 多用户会话隔离：基于浏览器 Cookie 的 session ID，存档独立存储在 `data/sessions/<session_id>/`
  - 新增 `lonely-world-web` 启动命令
  - 新增 `pyproject.toml` 可选依赖 `[web]`（FastAPI、Uvicorn）

### 计划添加

- 支持多角色互动
- 添加音效和背景音乐
- 支持多语言（英文、日文等）

## [0.2.0] - 2025-04-01

### 新增

- **多 LLM 提供商支持**
  - 抽象 LLM Provider 层，统一接口 `chat_text()` / `chat_json()` / `chat_text_async()` / `chat_json_async()`
  - 支持 OpenAI、Anthropic Claude、Ollama / vLLM 等兼容接口
  - 可通过 `--provider` 参数或配置文件切换
- **角色管理增强**
  - 启动时自动列出所有存档角色，支持数字快速选择
  - 可直接输入新角色名称创建角色
  - 支持 `d` 删除角色、`r` 重命名角色
  - CLI 新增 `--delete-character <名称>` 参数
- **CLI 体验升级**
  - 集成 `rich`：彩色面板、进度 spinner、蓝色边框角色回复
  - 游戏内输入 `help` / `?` 查看彩色命令帮助面板
  - 输入 `undo` / `撤回` 可撤销上一轮，保留最近 10 条历史快照
- **文学续写可选开关**
  - 新增配置项 `enable_story_append`，默认关闭
  - CLI 支持 `--story-append` 临时开启
  - 关闭后每次交互仅调用 1 次 LLM，显著降低成本与延迟
- **Token-aware 动态上下文截断**
  - 新建 `lonely_world/game/memory.py`，默认 6000 token 预算
  - 从最新对话向旧对话回溯，在预算内保留尽可能多的 exchanges
- **自动记忆压缩归档**
  - 对话超过 30 轮时，自动调用 LLM 将早期对话压缩为 100-200 字摘要
  - 摘要追加到 `memory_summary`，同时释放 Token 预算
- **API 错误自动重试与分类提示**
  - 对网络抖动、超时、频率限制自动重试 2 次（指数退避）
  - 输出中文友好错误提示：认证失败、连接失败、超时、参数错误等
- **API Key 安全存储**
  - 集成 `keyring`，优先使用系统密钥环存储 API Key
  - 自动迁移旧版明文 `data/config.json` 中的密钥到密钥环
  - 若密钥环不可用，回退到明文存储并给出明确警告
- **存档 Schema 版本控制**
  - `Character` 新增 `schema_version="2"`
  - `from_dict()` 自动检测 v1 旧存档并迁移（补充 `world.notes` 等默认值）
- **日志系统**
  - 引入标准库 `logging`
  - CLI 支持 `--verbose` 查看详细调用日志

### 变更

- **架构重构**：将 `main.py` 拆分为 `lonely_world/` 包结构
  - `config.py`：配置管理（含 keyring 集成）
  - `storage.py`：文件存储与角色管理
  - `llm/`：LLM Provider 抽象、实现、重试机制
  - `game/`：游戏循环、世界观构建、记忆管理
  - `models.py`：数据模型（含 schema 迁移）
  - `cli.py`：命令行入口
- **入口文件**：`main.py` 精简为入口存根
- **版本要求**：维持 `requires-python = ">=3.10"`

### 安全

- API Key 存储优化：优先使用系统密钥环（keyring），回退到明文存储时给出明确警告
- 维持环境变量配置优先级高于本地文件
- 旧版明文密钥自动迁移到密钥环并清空配置文件中的敏感字段

## [0.1.0] - 2025-01-XX

### 新增

- 核心游戏功能
  - 无预设剧情的文字冒险游戏
  - 5 轮问答构建世界观
  - 角色长期状态保存（物品、技能、性格等）
  - 故事自动续写功能
- 配置管理
  - 支持环境变量配置（`OPENAI_API_KEY`、`LONELY_WORLD_API_KEY` 等）
  - 本地配置文件存储（`data/config.json`）
- 存档系统
  - 角色存档（`data/characters/<角色名>/character.json`）
  - 故事全文保存（`data/characters/<角色名>/story.md`）
  - 导出功能（故事导出、角色导出）
- 用户界面
  - 中文命令行界面
  - 快捷命令支持（退出、故事、导出等）
- 开发支持
  - MIT 开源许可证
  - pyproject.toml 项目配置
  - 代码规范配置（ruff、mypy）
  - 测试框架配置（pytest）

### 安全

- API Key 明文存储警告提示
- 敏感数据目录默认忽略（`.gitignore`）

---

## 版本说明

- **[Unreleased]**: 开发中的功能
- **[0.2.0]**: 架构重构、多模型支持、CLI 体验升级与核心机制深化
- **[0.1.0]**: 首个公开发布版本

[Unreleased]: https://github.com/panna-arts/lonely-world/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/panna-arts/lonely-world/releases/tag/v0.2.0
[0.1.0]: https://github.com/panna-arts/lonely-world/releases/tag/v0.1.0
