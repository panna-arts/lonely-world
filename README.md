## lonely world 孤独世界

一款中文命令行文字探险游戏。没有既定故事线，所有故事由玩家输入与智能体互动推进。角色的物品、技能、性格与世界观等长期状态会永久保留在本地。

### 主要特性

- **无预设剧情**：由玩家输入驱动情节发展。
- **世界观共创**：启动时 5 轮问答构建时间、地点、人物与社会风貌。
- **长期记忆与存档**：角色状态与世界观永久保存，可随时续玩。
- **模型可配置**：支持自定义 `API Key`、`Base URL` 与 `model`。

### 环境要求

- **Python**：3.10 及以上
- **网络**：可访问所配置的模型服务

### 快速开始

1. **安装依赖**：
   - `python3 -m pip install -r requirements.txt`
2. **启动游戏**：
   - `python3 main.py`

首次启动将提示输入：
- **API Key**
- **API Base URL**（例如 `https://www.dmxapi.cn/v1`）
- **模型名称**（例如 `gpt-5-mini`）
- **角色名称**

### 配置方式

启动时输入的配置将保存到 `data/config.json`，下次启动默认读取并可回车沿用。

- **环境变量优先**：
  - `OPENAI_API_KEY` 或 `LONELY_WORLD_API_KEY`
  - `OPENAI_BASE_URL` 或 `LONELY_WORLD_BASE_URL`
  - `LONELY_WORLD_MODEL`
- **本地存档**：
  - `data/config.json`：模型配置
  - `data/characters/`：角色存档与长期记忆

### 游戏流程

- **新角色**：进行 5 轮问答构建世界观。
- **续玩角色**：自动加载存档继续故事。
- **退出保存**：输入 `退出` / `quit` / `exit` 保存并结束。

### 常见问题

- **提示 `ModuleNotFoundError: No module named 'openai'`**：
  - 运行 `python3 -m pip install -r requirements.txt`
- **提示 `401 invalid_api_key`**：
  - 检查 `API Key` 是否有效，或在环境变量/`data/config.json` 中更新
- **无法访问模型**：
  - 确认 `Base URL` 与网络环境正确

### 安全提示

- **请勿把 `API Key` 提交到公开仓库**。
- 建议优先使用环境变量配置密钥。
