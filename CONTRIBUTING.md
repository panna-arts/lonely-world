# 贡献指南

感谢你考虑为 **lonely world 孤独世界** 做出贡献！

## 如何贡献

### 报告问题

如果你发现了 bug 或有新功能建议，请：

1. 在 [Issues](https://github.com/panna-arts/lonely-world/issues) 中搜索，确认问题未被报告
2. 创建新 Issue，包含：
   - 清晰的标题和描述
   - 复现步骤（如果是 bug）
   - 期望行为和实际行为
   - 你的环境信息（Python 版本、操作系统等）
   - 相关日志或截图

### 提交代码

#### 1. Fork 并克隆仓库

```bash
git clone https://github.com/YOUR_USERNAME/lonely-world.git
cd lonely-world
```

#### 2. 创建开发环境

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"
```

若需测试 Anthropic 支持，额外安装：

```bash
pip install -e ".[anthropic]"
```

#### 3. 创建功能分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 4. 进行开发

- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档（README、CHANGELOG 等）

#### 5. 运行测试和检查

```bash
pytest --cov=lonely_world --cov-report=term-missing
ruff check .
ruff format --check .
mypy lonely_world
```

#### 6. 提交更改

使用清晰的提交信息：

```bash
git add .
git commit -m "feat: 添加新功能描述"
# 或
git commit -m "fix: 修复某个问题"
# 或
git commit -m "docs: 更新文档"
```

提交信息格式：
- `feat:` 新功能
- `fix:` 修复 bug
- `docs:` 文档更新
- `style:` 代码格式调整（不影响功能）
- `refactor:` 代码重构
- `test:` 测试相关
- `chore:` 构建/工具相关

#### 7. 推送并创建 Pull Request

```bash
git push origin feature/your-feature-name
```

然后在 GitHub 上创建 Pull Request。

## 开发规范

### 代码风格

- 使用 [ruff](https://github.com/astral-sh/ruff) 进行代码格式化和检查
- 遵循 PEP 8 规范
- 行长度不超过 100 字符
- 使用有意义的变量和函数名

### 类型注解

- 为函数添加类型注解
- 使用 `mypy` 进行类型检查

### 测试

- 为新功能添加测试
- 确保所有测试通过
- 保持合理的测试覆盖率（建议 >= 85%）

### 文档

- 更新 README.md（如果需要）
- 更新 CHANGELOG.md
- 添加必要的代码注释

## 项目结构

```
lonely-world/
├── main.py                 # 入口文件（精简）
├── lonely_world/           # 核心包
│   ├── __init__.py
│   ├── cli.py              # 命令行入口与参数解析
│   ├── config.py           # 配置加载、环境变量与 keyring 处理
│   ├── logging_config.py   # 日志配置
│   ├── models.py           # 数据模型（Character、World、GameConfig 及 schema 迁移）
│   ├── storage.py          # 文件存储与角色管理
│   ├── game/               # 游戏逻辑
│   │   ├── __init__.py
│   │   ├── engine.py       # UI-agnostic 游戏引擎
│   │   ├── loop.py         # CLI 适配层（调用 engine）
│   │   ├── memory.py       # Token-aware 截断 + 自动归档
│   │   ├── prompts.py      # 系统 Prompt 管理
│   │   └── world.py        # 世界观构建
│   ├── llm/                # LLM 抽象层
│   │   ├── __init__.py
│   │   ├── base.py         # Provider 抽象接口（含异步接口）
│   │   ├── factory.py      # Provider 工厂
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   └── retry.py        # 错误分类 + 自动重试（含异步）
│   └── web/                # Web UI（FastAPI）
│       ├── __init__.py
│       ├── main.py         # FastAPI 应用入口
│       ├── session.py      # Session 状态管理
│       ├── api.py          # REST + SSE 路由
│       ├── storage.py      # 会话隔离存储
│       └── events.py       # SSE 格式化
├── tests/                  # 测试文件
├── data/                   # 游戏数据（不提交到仓库）
├── web_static/             # Web 前端（HTML/CSS/JS）
│   ├── index.html
│   ├── style.css
│   └── app.js
├── docs/                   # 文档和截图
│   ├── README.md
│   ├── demo-session.txt
│   └── IMPLEMENTATION_SUMMARY.md
├── README.md               # 项目说明
├── CONTRIBUTING.md         # 贡献指南
├── CHANGELOG.md            # 变更记录
├── CODE_OF_CONDUCT.md      # 行为准则
├── LICENSE                 # 许可证
├── pyproject.toml          # 项目配置
└── requirements.txt        # 依赖列表
```

### 新增模块时的注意事项

- **数据模型**：所有可序列化的数据结构优先放入 `models.py`，并为 schema 升级预留版本字段
- **LLM 支持**：若需接入新的模型提供商，继承 `llm/base.py` 中的 `LLMProvider`（同步 + 异步接口），并在 `llm/factory.py` 注册
- **游戏逻辑**：与玩家交互相关的代码放入 `game/` 包，避免在 `cli.py` 中堆积业务逻辑。核心逻辑优先放入 `game/engine.py`，CLI 和 Web 均调用 engine
- **存储操作**：CLI 侧文件 I/O 统一通过 `storage.py`；Web 侧使用 `web/storage.py` 的 `SessionStorage` 以保持多用户隔离。所有本地数据默认存放在 `local/data/`，已加入 `.gitignore`
- **Web UI**：前端静态资源放在 `web_static/`，后端路由放在 `web/api.py`。新增 API 需同步补充 `tests/test_web_api.py` 用例

## 行为准则

- 尊重所有贡献者
- 保持友好和建设性的讨论
- 接受建设性批评
- 关注对社区最有利的事情

## 需要帮助？

如果你有任何问题，可以：

- 在 [Discussions](https://github.com/panna-arts/lonely-world/discussions) 中提问
- 在 Issue 中留言

再次感谢你的贡献！🎉
