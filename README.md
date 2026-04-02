# lonely world 孤独世界

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

一款中文 AI 文字冒险游戏。没有既定故事线，所有故事由玩家输入与智能体互动推进。角色的物品、技能、性格与世界观等长期状态会永久保留在本地。

> **v0.2.0 新特性**：支持多 LLM 提供商（OpenAI / Claude / Ollama）、角色列表快速选择、文学续写可选开关、API Key 系统密钥环存储、Token-aware 长记忆、自动重试与中文错误提示、游戏内帮助/撤销/删除命令。
>
> **Web UI（新增）**：现在可以通过浏览器访问游戏，支持多用户独立存档、流式对话、世界观分步构建。

```
已存在角色：
  1. 李逍遥
  2. 林月如
  0. 创建新角色
  d. 删除角色
  r. 重命名角色

请选择角色编号（或输入 d/r）：1
已载入角色：李逍遥

上次对话回顾：
你：推门走进客栈。
李逍遥：客栈里灯火昏黄，几个江湖客正在低声交谈……

进入游戏
输入 help 查看可用命令，quit 保存并退出。

你：
```

*更多演示请查看 [docs/demo-session.txt](docs/demo-session.txt)*  
*完整改进记录请查看 [docs/IMPLEMENTATION_SUMMARY.md](docs/IMPLEMENTATION_SUMMARY.md)*

## 主要特性

- **无预设剧情**：由玩家输入驱动情节发展，每次游戏都是独特体验
- **世界观共创**：启动时 5 轮问答构建时间、地点、人物与社会风貌
- **长期记忆与存档**：角色状态与世界观永久保存，可随时续玩
- **故事自动续写**（可选）：开启后每次互动生成文学续写并保存到 `story.md`
- **多模型支持**：OpenAI、Anthropic Claude、Ollama / vLLM 等兼容 OpenAI 接口的模型
- **角色管理**：启动时列出所有存档角色，支持快速切换、删除、重命名
- **长剧情记忆**：Token-aware 动态截断 + 自动记忆压缩归档，避免"失忆"
- **稳定连接**：API 错误自动分类，网络抖动自动重试 2 次
- **彩色交互**：`rich` 驱动的进度 spinner、边框面板、帮助界面
- **Web UI**：通过浏览器访问，支持多用户会话、Markdown 渲染、角色管理与快捷操作

## 环境要求

- **Python**：3.10 及以上
- **网络**：可访问所配置的模型服务（本地模型除外）

## 快速开始

### 方式一：直接运行

```bash
git clone https://github.com/panna-arts/lonely-world.git
cd lonely-world
python3 -m pip install -r requirements.txt
python3 main.py
```

### 方式二：通过 pip 安装（推荐）

```bash
pip install lonely-world
lonely-world
```

### 方式三：使用 Anthropic Claude

```bash
pip install lonely-world[anthropic]
lonely-world --provider anthropic --model claude-3-opus
```

### 方式四：启动 Web UI（浏览器访问）

```bash
pip install -e ".[web]"
lonely-world-web
```

打开浏览器访问 `http://localhost:7860` 即可开始游戏。Web UI 支持多用户同时在线，每个用户的存档独立保存在 `data/sessions/<session_id>/` 下。

> **注意**：Web 模式需要预先配置好环境变量（`OPENAI_API_KEY`、`OPENAI_BASE_URL`、`LONELY_WORLD_MODEL`），不会进行交互式提示。

首次启动将提示输入 API Key、Base URL 和模型名称。**API Key 会优先存入系统密钥环**（keyring），若不可用才会保存到 `data/config.json`。

## 命令行参数

```bash
lonely-world [选项]
```

| 参数 | 说明 |
|------|------|
| `--version`, `-v` | 显示版本号 |
| `--verbose` | 启用详细日志输出 |
| `--story-append` | 本次启动启用文学续写 |
| `--provider <名称>` | 指定 LLM 提供商：`openai` / `anthropic` / `ollama` |
| `--model <名称>` | 指定模型名称，如 `gpt-4`、`claude-3-opus` |
| `--delete-character <名称>` | 直接删除指定角色 |

## 环境变量

以下环境变量优先级最高：

- `OPENAI_API_KEY` 或 `LONELY_WORLD_API_KEY`
- `OPENAI_BASE_URL` 或 `LONELY_WORLD_BASE_URL`
- `LONELY_WORLD_MODEL`

## 本地存档

- `local/data/config.json`：模型配置（含 `provider`、`enable_story_append` 等），**不再保存 API Key**（若密钥环可用）
- `local/data/characters/<角色名>/character.json`：CLI 角色存档（含 `schema_version`）
- `local/data/characters/<角色名>/story.md`：CLI 故事全文
- `local/data/sessions/<session_id>/characters/<角色名>/character.json`：Web UI 角色存档
- `local/data/characters/<角色名>/expert/story/`：故事导出副本
- `local/data/characters/<角色名>/expert/characters/`：角色导出汇总

## 游戏内命令

| 命令 | 说明 |
|------|------|
| `help` / `?` | 显示可用命令帮助面板 |
| `undo` / `撤回` | 撤销上一轮输入并恢复状态 |
| `退出` / `quit` / `exit` | 保存并结束游戏 |
| `故事` / `story` | 查看 `story.md` 最近片段 |
| `导出故事` / `export` | 导出故事副本 |
| `导出角色` / `export-role` | 导出角色汇总信息 |

## 配置示例

`data/config.json`：

```json
{
  "api_key": "",
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4",
  "provider": "openai",
  "enable_story_append": false
}
```

> 注意：`api_key` 字段在密钥环可用时会被自动清空，密钥实际存储在操作系统密钥环中。所有本地生成数据均存放在 `local/` 目录，已默认加入 `.gitignore`，避免误提交到仓库。

## 常见问题

### 提示 `ModuleNotFoundError: No module named 'openai'`

运行 `python3 -m pip install -r requirements.txt`，若使用 Claude 则额外安装 `pip install anthropic`。

### 提示 `401 invalid_api_key`

检查 API Key 是否有效，或在环境变量 / 系统密钥环 / `local/data/config.json` 中更新。

### 无法访问模型

确认 `Base URL` 与网络环境正确。本地模型请确保 Ollama / vLLM 服务已启动。

## 安全提示

- ⚠️ **请勿把 `API Key` 提交到公开仓库**
- ✅ **API Key 优先存储在系统密钥环**（macOS Keychain / Windows Credential / Linux Secret Service）
- ⚠️ 若密钥环不可用，才会以明文存储在 `data/config.json`，建议：
  - 使用环境变量配置密钥（优先级最高）
  - 定期更换密钥
  - 不要在公共计算机上保存密钥
- 导出内容可能包含敏感上下文，已默认忽略 `data/characters/**/expert/`，避免上传到 GitHub

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest --cov=lonely_world --cov-report=term-missing
```

### 代码检查

```bash
ruff check .
ruff format --check .
mypy lonely_world
```

## 贡献

欢迎贡献代码、报告问题或提出建议！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 变更记录

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 许可证

本项目采用 [MIT 许可证](LICENSE) 开源。

## 致谢

- 感谢 [OpenAI](https://openai.com/) 与 [Anthropic](https://www.anthropic.com/) 提供强大的语言模型 API
- 感谢所有贡献者和玩家的支持与反馈

## 路线图

- [x] 支持更多 LLM 提供商（Claude、Ollama 等）
- [x] API 错误自动重试与分类提示
- [x] Token-aware 动态上下文与记忆压缩
- [x] 异步 LLM 接口
- [x] 添加图形界面（Web UI）
- [ ] 支持多角色互动
- [ ] 添加音效和背景音乐
- [ ] 支持多语言（英文、日文等）

---

**愿你在孤独的世界中，找到属于自己的故事。**
