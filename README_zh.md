# Databricks Notebooks Skill for Claude Code

[English](README.md) | 中文

一个 [Claude Code](https://claude.ai/claude-code) 技能，支持直接在命令行中读取和编辑 Databricks notebooks，并可浏览 Unity Catalog schema 用于智能代码生成。

## 功能特性

- 列出、导出、导入和删除 Databricks notebooks
- 支持 cell 级别的编辑
- 浏览 Unity Catalog schema 辅助代码生成
- 导入后自动验证，检测保存失败的情况

## 安装

### 1. 将 skill 复制到你的项目

将 `.claude/skills/databricks-notebooks` 目录复制到你的项目：

```bash
# 克隆此仓库
git clone https://github.com/zengjie/databricks-notebooks-skill.git

# 复制 skill 到你的项目
cp -r databricks-notebooks-skill/.claude/skills/databricks-notebooks YOUR_PROJECT/.claude/skills/
```

或者添加为 git submodule：

```bash
git submodule add https://github.com/zengjie/databricks-notebooks-skill.git .claude/skills/databricks-notebooks-skill
```

### 2. 运行安装脚本

```bash
bash .claude/skills/databricks-notebooks/setup.sh
```

这将：
- 在 `.venv/` 创建虚拟环境
- 安装依赖 (databricks-sdk, python-dotenv)
- 从模板创建 `.env` 文件
- 测试连接

### 3. 配置 Databricks 凭证

编辑项目根目录的 `.env` 文件：

```bash
DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
DATABRICKS_TOKEN=dapi...
```

或运行交互式配置：

```bash
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/config_helper.py setup
```

## 在 Claude Code 中使用

安装后，skill 将自动在 Claude Code 中可用。你可以直接让 Claude：

- **"列出我的 Databricks notebooks"**
- **"编辑 Playground notebook"**
- **"创建一个叫 analytics 的新 notebook"**
- **"查看 main.sales.customers 表的结构"**
- **"添加一个 SQL cell 查询 users 表"**

### 对话示例

```
你: 编辑我的 Databricks Playground notebook

Claude: 让我导出 Playground notebook...
[导出 notebook，显示内容]

你: 添加一个 cell 查询 users 表最新的 10 条记录

Claude: [获取表结构，添加新的 SQL cell，导入并验证]
完成！已添加查询的新 cell。
```

## 手动 CLI 使用

你也可以直接使用脚本：

```bash
# 列出 notebooks
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py list "/Users/you@example.com/"

# 导出 notebook
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py export "/Users/you@example.com/notebook"

# 导入 notebook（自动验证）
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/databricks_client.py import "/Users/you@example.com/notebook" \
    -f content.py -l PYTHON

# 浏览 Unity Catalog
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py schemas prod
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py tables prod myschema
.venv/bin/python3 .claude/skills/databricks-notebooks/scripts/catalog_client.py table-schema prod.myschema.mytable
```

## 项目结构

```
.claude/skills/databricks-notebooks/
├── SKILL.md                 # Skill 定义和完整文档
├── .env.example             # 配置模板
├── setup.sh                 # 一键安装脚本
└── scripts/
    ├── databricks_client.py # Notebook 增删改查操作
    ├── catalog_client.py    # Unity Catalog schema 浏览
    ├── config_helper.py     # Databricks 配置管理
    ├── notebook_parser.py   # Cell 级别编辑工具
    └── requirements.txt     # Python 依赖
```

## 文档

查看 [SKILL.md](.claude/skills/databricks-notebooks/SKILL.md) 获取完整文档，包括：

- 所有可用命令
- Notebook SOURCE 格式参考
- Cell 级别编辑工作流
- Unity Catalog 浏览
- 故障排除指南

## 许可证

MIT
