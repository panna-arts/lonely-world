# lonely world 孤独世界

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

一款中文命令行文字探险游戏。没有既定故事线，所有故事由玩家输入与智能体互动推进。角色的物品、技能、性格与世界观等长期状态会永久保留在本地。

![游戏截图](docs/screenshot.png)
*游戏截图占位 - 建议添加实际游戏运行的 GIF 或截图*

## 主要特性

- **无预设剧情**：由玩家输入驱动情节发展，每次游戏都是独特体验
- **世界观共创**：启动时 5 轮问答构建时间、地点、人物与社会风貌
- **长期记忆与存档**：角色状态与世界观永久保存，可随时续玩
- **故事自动续写**：每次互动后生成文学续写并保存到 `story.md`
- **模型可配置**：支持自定义 `API Key`、`Base URL` 与 `model`

## 环境要求

- **Python**：3.10 及以上
- **网络**：可访问所配置的模型服务

## 快速开始

### 方式一：直接运行

1. **克隆仓库**：
   ```bash
   git clone https://github.com/panna-arts/lonely-world.git
   cd lonely-world
   ```

2. **安装依赖**：
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **启动游戏**：
   ```bash
   python3 main.py
   ```

### 方式二：通过 pip 安装（推荐）

```bash
pip install lonely-world
lonely-world
```

首次启动将提示输入：
- **API Key**
- **API Base URL**（例如 `https://api.openai.com/v1`）
- **模型名称**（例如 `gpt-4`）
- **角色名称**

## 配置方式

启动时输入的配置将保存到 `data/config.json`，下次启动默认读取并可回车沿用。

### 环境变量优先

- `OPENAI_API_KEY` 或 `LONELY_WORLD_API_KEY`
- `OPENAI_BASE_URL` 或 `LONELY_WORLD_BASE_URL`
- `LONELY_WORLD_MODEL`

### 本地存档

- `data/config.json`：模型配置
- `data/characters/<角色名>/character.json`：角色存档
- `data/characters/<角色名>/story.md`：故事全文

### 导出目录（按角色隔离）

- `data/characters/<角色名>/expert/story/`：故事导出副本
- `data/characters/<角色名>/expert/characters/`：角色导出汇总信息

## 游戏流程

- **新角色**：进行 5 轮问答构建世界观
- **续玩角色**：自动加载存档继续故事
- **退出保存**：输入 `退出` / `quit` / `exit` 保存并结束
- **查看故事摘要**：输入 `故事` / `story` 查看最近片段
- **导出故事**：输入 `导出故事` / `export` 导出全文副本（保存到 `data/characters/<角色名>/expert/story/`）
- **导出角色**：输入 `导出角色` / `export-role` 导出角色汇总信息（保存到 `data/characters/<角色名>/expert/characters/`）

## 常见问题

### 提示 `ModuleNotFoundError: No module named 'openai'`

运行 `python3 -m pip install -r requirements.txt`

### 提示 `401 invalid_api_key`

检查 `API Key` 是否有效，或在环境变量/`data/config.json` 中更新

### 无法访问模型

确认 `Base URL` 与网络环境正确

## 安全提示

- ⚠️ **请勿把 `API Key` 提交到公开仓库**
- ⚠️ **API Key 会明文存储在本地 `data/config.json`**，建议：
  - 使用环境变量配置密钥（优先级更高）
  - 定期更换密钥
  - 不要在公共计算机上保存密钥
- 导出内容可能包含敏感上下文，已默认忽略 `data/characters/**/expert/`，避免上传到 GitHub
- 建议优先使用环境变量配置密钥

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码检查

```bash
ruff check .
mypy main.py
```

## 贡献

欢迎贡献代码、报告问题或提出建议！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 变更记录

查看 [CHANGELOG.md](CHANGELOG.md) 了解版本更新历史。

## 许可证

本项目采用 [MIT 许可证](LICENSE) 开源。

## 致谢

- 感谢 [OpenAI](https://openai.com/) 提供强大的语言模型 API
- 感谢所有贡献者和玩家的支持与反馈

## 路线图

- [ ] 支持更多 LLM 提供商（Claude、Gemini 等）
- [ ] 添加图形界面（Web UI）
- [ ] 支持多角色互动
- [ ] 添加音效和背景音乐
- [ ] 支持多语言（英文、日文等）

---

**愿你在孤独的世界中，找到属于自己的故事。**
