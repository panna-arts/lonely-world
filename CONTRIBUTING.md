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

#### 3. 创建功能分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

#### 4. 进行开发

- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档

#### 5. 运行测试和检查

```bash
pytest
ruff check .
mypy main.py
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
- 保持合理的测试覆盖率

### 文档

- 更新 README.md（如果需要）
- 更新 CHANGELOG.md
- 添加必要的代码注释

## 项目结构

```
lonely-world/
├── main.py              # 主程序入口
├── tests/               # 测试文件
├── data/                # 游戏数据（不提交到仓库）
├── docs/                # 文档和截图
├── README.md            # 项目说明
├── CONTRIBUTING.md      # 贡献指南
├── CHANGELOG.md         # 变更记录
├── LICENSE              # 许可证
├── pyproject.toml       # 项目配置
└── requirements.txt     # 依赖列表
```

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
