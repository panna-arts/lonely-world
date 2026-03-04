# 变更记录

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [Unreleased]

### 计划添加

- 支持更多 LLM 提供商（Claude、Gemini 等）
- 添加图形界面（Web UI）
- 支持多角色互动
- 添加音效和背景音乐
- 支持多语言（英文、日文等）

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
- **[0.1.0]**: 首个公开发布版本

[Unreleased]: https://github.com/panna-arts/lonely-world/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/panna-arts/lonely-world/releases/tag/v0.1.0
