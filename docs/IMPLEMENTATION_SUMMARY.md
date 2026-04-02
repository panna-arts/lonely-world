# lonely-world 综合改进实施记录

**记录日期**：2025-04-01  
**涉及版本**：v0.1.0 → v0.2.0  
**执行策略**：方案 C（文档整理）→ 方案 A（体验增强）→ 方案 B（机制深化）

---

## 一、方案 C：文档整理与社区运营

### 1.1 文档更新

| 文件 | 变更内容 |
|------|----------|
| `README.md` | 全面重写为 v0.2.0 版本，新增多 LLM 支持说明、keyring 安全提示、`--story-append` 开关、角色管理、CLI 参数表、环境变量说明、游戏内命令表 |
| `CHANGELOG.md` | 正式发布 `[0.2.0] - 2025-04-01`，记录架构重构、多模型支持、角色管理、CLI 升级、文学续写开关、日志系统、记忆压缩、错误重试、keyring、schema 版本、异步接口等变更 |
| `CONTRIBUTING.md` | 更新为新模块架构的说明，修正 `mypy lonely_world` 等开发命令，补充新增 LLM Provider 的指引，覆盖率标准建议 >= 85% |
| `docs/demo-session.txt` | 新增终端会话文本演示，展示角色选择、世界观问答、游戏对话的完整流程 |

### 1.2 CI/CD 修复

- **`.github/workflows/ci.yml`**
  - `mypy main.py` → `mypy lonely_world`
  - `pytest --cov=main` → `pytest --cov=lonely_world`

### 1.3 GitHub 社区模板

| 文件 | 用途 |
|------|------|
| `.github/ISSUE_TEMPLATE/bug_report.yml` | Bug 报告模板 |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | 功能建议模板 |
| `.github/ISSUE_TEMPLATE/config.yml` | Issue 模板配置，链接到 Discussions |
| `.github/pull_request_template.md` | PR 描述模板，含检查清单 |
| `CODE_OF_CONDUCT.md` | 贡献者行为准则（基于 Contributor Covenant） |

---

## 二、方案 A：产品体验全面升级

### 2.1 CLI 视觉增强（`rich`）

- **启动面板**：进入游戏时显示带边框的彩色提示面板
- **进度提示**：LLM 调用时显示 `正在构思故事…` spinner；文学续写时显示 `正在续写文学片段…`
- **彩色回复**：角色回复使用蓝色边框 `Panel` 输出，故事摘要使用洋红色边框
- **世界观问答**：问题编号使用 `[bold yellow]` 高亮

### 2.2 帮助系统

- 游戏内输入 `help` / `?` / `/help` 即可查看所有可用命令的彩色帮助面板
- 启动提示中也会提醒玩家如何调用帮助

### 2.3 角色管理功能补齐

- 启动角色列表新增操作：
  - `d` → 删除角色（需要二次确认）
  - `r` → 重命名角色
- CLI 新增 `--delete-character <名称>` 参数，支持命令行直接删除角色
- 对应存储层新增 `delete_character()` 和 `rename_character()` 函数

### 2.4 Undo 撤销机制

- 游戏内输入 `undo` / `撤回` / `/undo` 可撤销上一轮输入
- 自动恢复角色状态、对话记录、世界观和记忆摘要
- 保留最近 **10 条**历史快照，超出时自动丢弃最旧记录

### 2.5 依赖更新

- `pyproject.toml` 新增依赖：`rich>=13.0.0`

---

## 三、方案 B：核心机制深化

### 3.1 API 错误分类与自动重试

- 新建模块：`lonely_world/llm/retry.py`
- 提供 `@with_retry(max_retries=2, base_delay=1.0)` 装饰器，对以下错误自动重试（指数退避）：
  - 网络连接失败（`APIConnectionError`、`ConnectionError`、`ConnectTimeout`）
  - 请求超时（`APITimeoutError`、`TimeoutError`、`ReadTimeout`）
  - 调用频率超限（`RateLimitError`）
- 错误分类输出中文友好提示：
  - 认证失败 → 检查 API Key
  - 频率超限 → 请稍后重试
  - 连接失败 → 检查网络与 Base URL
  - 超时 → 网络不稳定或模型响应慢
  - 参数错误 → 检查模型名或上下文长度
- `OpenAIProvider` 和 `AnthropicProvider` 的 `chat_text()` / `chat_json()` 均已集成重试

### 3.2 Token-aware 动态上下文截断

- 新建模块：`lonely_world/game/memory.py`
- 替换原来粗暴的固定 `[-12:]` 截断
- 采用 **Token 预算制**（默认 6000 tokens），从最新对话向旧对话回溯，在预算范围内保留尽可能多的 exchanges
- 估算策略：保守按 `1.5 tokens/字符` 计算，每条消息额外加 10 token 格式开销

### 3.3 自动记忆压缩机制

- 触发阈值：对话轮数超过 **30 轮**
- 归档流程：
  1. 取最早的一半对话记录
  2. 调用 LLM 生成 100-200 字的叙事摘要
  3. 将摘要追加到 `character.memory_summary`
  4. 从 `character.conversation` 中移除已归档记录
- 释放 Token 预算的同时，保留关键事件、人物关系和地点变化
- Prompt 同步更新，明确告知叙事智能体必须依据 `长期记忆摘要` 保持剧情连贯

---

## 四、追加记录：热修复 + 方案 C（工程稳健）

**执行时间**：2025-04-01 后续  
**涉及版本**：v0.2.0（维护与质量强化）

### 4.1 热修复

| 文件 | 变更内容 |
|------|----------|
| `CHANGELOG.md` | 修正 `Unreleased`，移除已在 v0.2.0 实现的 "Token-aware 动态上下文截断" 和 "自动记忆压缩与归档" |
| `ENGINEERING.md` | 添加提示，说明本文档主要记录 v0.1.0 阶段工程化过程，v0.2.0+ 改进见本摘要文档 |

### 4.2 API Key 安全存储（keyring）

- `pyproject.toml` 新增依赖 `keyring>=25.0.0`
- `lonely_world/config.py` 改进 API Key 读取逻辑：
  - 优先级：环境变量 → 系统密钥环（keyring）→ 本地配置文件
  - 首次输入密钥后优先存入系统密钥环（macOS Keychain / Windows Credential / Linux Secret Service）
  - 若密钥环不可用，回退到明文存储并给出警告
  - 自动迁移：检测到配置文件中有明文密钥且密钥环为空时，自动迁移到密钥环并清空配置文件中的密钥字段

### 4.3 存档 Schema 版本控制

- `Character` 数据模型新增 `schema_version` 字段（当前为 `"2"`）
- `Character.from_dict()` 增加版本检测与自动迁移逻辑
  - v1 → v2：为 `world.notes` 补充默认空列表，确保旧存档兼容性
- 为未来格式升级奠定基础，避免老存档无法读取

### 4.4 异步 LLM 调用支持

- `LLMProvider` 抽象层新增 `chat_text_async()` / `chat_json_async()` 接口
- `OpenAIProvider` 集成 `AsyncOpenAI` 客户端
- `AnthropicProvider` 集成 `AsyncAnthropic` 客户端
- `retry.py` 新增 `@with_retry_async` 装饰器，为异步调用提供相同的指数退避重试能力
- 为后续 Web UI / TUI 开发解除性能瓶颈

### 4.5 测试覆盖率补齐

- 新建/扩展测试文件：
  - `tests/test_config.py`：覆盖 keyring 迁移、环境变量、prompt 回退、空输入退出
  - `tests/test_world.py`：覆盖世界观构建全流程
  - `tests/test_retry.py`：覆盖 `@with_retry_async` 的多种场景
  - `tests/test_llm.py`：覆盖 Anthropic Provider 和 OpenAI 异步接口
  - `tests/test_storage.py`：覆盖 legacy 迁移、角色路径、空存档、删除/重命名边界
  - `tests/test_openai_provider.py`：覆盖 `_parse_json` 的边界情况
  - `tests/test_game_loop.py`：扩展帮助、导出命令的测试
  - `tests/test_models.py`：覆盖 schema version 迁移
- **最终指标**：
  - 测试数量：**100 个全部通过**
  - 测试覆盖率：**89%**

---

## 五、最终项目状态

### 5.1 代码结构

```
lonely-world/
├── main.py                          # 6 行入口文件
├── lonely_world/
│   ├── __init__.py
│   ├── cli.py                       # CLI 入口（rich 交互、参数解析）
│   ├── config.py                    # 配置管理（环境变量、keyring 安全存储）
│   ├── logging_config.py            # 日志配置
│   ├── models.py                    # 数据模型（含 schema_version 迁移）
│   ├── storage.py                   # 文件存储与角色管理
│   ├── game/
│   │   ├── __init__.py
│   │   ├── loop.py                  # 游戏主循环（help / undo / 记忆压缩触发）
│   │   ├── memory.py                # Token-aware 截断 + 自动归档
│   │   ├── prompts.py               # 系统 Prompt 管理
│   │   └── world.py                 # 世界观构建
│   └── llm/
│       ├── __init__.py
│       ├── base.py                  # Provider 抽象接口（含异步）
│       ├── factory.py               # Provider 工厂
│       ├── openai_provider.py       # OpenAI / OpenAI-compatible（含 AsyncOpenAI）
│       ├── anthropic_provider.py    # Anthropic Claude（含 AsyncAnthropic）
│       └── retry.py                 # 错误分类 + 自动重试（含异步）
├── tests/                           # 100 个测试
├── docs/
│   ├── README.md
│   ├── demo-session.txt
│   └── IMPLEMENTATION_SUMMARY.md    # 本文档
├── .github/
│   ├── workflows/ci.yml
│   ├── ISSUE_TEMPLATE/
│   ├── pull_request_template.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── LICENSE
└── pyproject.toml
```

### 5.2 质量指标

| 指标 | 结果 |
|------|------|
| 测试数量 | **100 个全部通过** |
| 测试覆盖率 | **89%** |
| 代码规范 | `ruff check .` ✅ |
| 代码格式化 | `ruff format --check .` ✅ |
| 类型检查 | `mypy lonely_world main.py` ✅ |

---

## 六、用户可感知的核心改进对比

| 维度 | 改进前（v0.1.0） | 改进后（v0.2.0） |
|------|------------------|------------------|
| **架构** | `main.py` 581 行一锅烩 | 模块化 `lonely_world/` 包 |
| **LLM 选择** | 仅 OpenAI | OpenAI / Claude / Ollama / vLLM |
| **API 成本** | 每次交互 2 次 LLM 调用 | 默认 1 次，可选手动开启续写 |
| **等待体验** | 黑屏干等 | spinner + 彩色面板 |
| **帮助系统** | 无 | `help` / `?` 彩色命令面板 |
| **角色管理** | 只能创建/加载 | 列出、删除、重命名、命令行删除 |
| **容错性** | 网络一抖就报错 | 自动重试 2 次，分类错误提示 |
| **撤销** | 无 | `undo` 撤回上一轮 |
| **长剧情记忆** | 固定 12 条对话，易失忆 | Token-aware 截断 + 自动记忆归档 |
| **API Key 安全** | 明文存储 | 优先系统密钥环，自动迁移 |
| **存档兼容** | 无版本标记 | `schema_version` + 自动迁移 |
| **开发者接口** | 仅同步 | 同步 + 异步统一接口 |
| **文档/社区** | 基础 README | 完整文档体系 + GitHub 模板 + 行为准则 |

---

## 七、方案 D：Web UI（FastAPI + SSE）

**执行时间**：2025-04-01 后续  
**涉及版本**：v0.2.0+（功能扩展）

### 7.1 目标与意义

- **突破圈层**：将 CLI 游戏扩展到浏览器，降低非技术用户门槛
- **多用户支持**：基于 session cookie 实现真正的多用户在线，各自独立存档
- **性能基础**：利用 v0.2.0 已完成的异步 LLM 接口，实现 SSE 流式响应

### 7.2 技术架构

| 层级 | 技术/文件 | 说明 |
|------|-----------|------|
| **前端** | `web_static/index.html + style.css + app.js` | 单页应用，左侧聊天、右侧状态面板 |
| **后端框架** | FastAPI + Uvicorn | 原生 async，支持 SSE |
| **会话管理** | `starlette SessionMiddleware` + `uuid` | 浏览器 Cookie 存储 session ID |
| **游戏核心** | `lonely_world/game/engine.py` | 从 `loop.py` 抽离的 UI-agnostic 引擎 |
| **世界观构建** | `lonely_world/game/world.py` | 新增 `WorldBuilder` 事件驱动状态机 |
| **存储隔离** | `lonely_world/web/storage.py` | `SessionStorage` 按 `session_id` 隔离存档 |

### 7.3 核心变更

- **新建 `lonely_world/game/engine.py`**：
  - `GameEngine` 类封装 `process_turn` / `process_turn_async` / `process_turn_stream`
  - 支持 snapshot/undo、story append、export、错误分类
  - `loop.py` 改为纯 CLI 适配层，100% 兼容原有行为
- **新建 `lonely_world/web/` 包**：
  - `main.py`：FastAPI 应用与 lifespan 事件
  - `session.py`：`SessionStore` 全局状态管理
  - `api.py`：REST + SSE 路由（`/api/chat`、`/api/undo`、`/api/create` 等）
  - `storage.py`：`SessionStorage` 文件 I/O
  - `events.py`：SSE 格式化辅助
- **前端 `web_static/`**：
  - 暗色主题、Markdown 渲染、打字机流式效果
  - 世界观构建分步弹窗、角色选择下拉框、快捷操作按钮

### 7.4 启动方式

```bash
pip install -e ".[web]"
lonely-world-web
```

访问 `http://localhost:7860`。

### 7.5 测试

- 新增 `tests/test_engine.py`：覆盖 GameEngine 同步/异步/流式接口
- 新增 `tests/test_web_api.py`：使用 `TestClient` 覆盖完整 API 流程（创建角色、世界观构建、聊天、undo、导出）
- 新增 `tests/test_web_storage.py`：覆盖 `SessionStorage` 的增删改查
- **全量测试**：123 个全部通过

---

## 八、后续建议

项目已具备长期迭代的健康基础，后续可考虑的优先级方向：

1. **音效与 BGM**：在关键剧情节点播放氛围音效，增强沉浸感
2. **多角色互动**：支持多个 AI 角色同时登场，玩家作为旁观者或参与者推动群像剧
3. **多语言**：界面与 Prompt 国际化，支持英文/日文等
4. **导出增强**：支持导出为 `.epub` 或 `.pdf`，让故事更容易分享

---

*愿你在孤独的世界中，找到属于自己的故事。*
