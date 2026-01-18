# 插件格式说明

## 插件目录结构

```
plugin-name/
├── share_plugins.json          # 插件元数据（必需）
├── commands/                  # 命令文件（可选）
│   ├── command1.md
│   └── command2.md
├── agents/                    # Agent 文件（可选）
│   ├── agent1.md
│   └── agent2.md
├── hooks.json                 # Hooks 配置（可选）
└── mcp.json                   # MCP 配置（可选）
```

## share_plugins.json 字段说明

```json
{
  "plugin": "插件名称（必需）",
  "version": "1.0.0",
  "description": "插件描述（可选）",
  "author": "作者名称（可选）",
  "license": "许可证（可选，默认 MIT）",
  "repository": {
    "type": "github/gitlab/custom",
    "url": "仓库 URL"
  },
  "content": {
    "commands": ["all"] 或 ["cmd1", "cmd2"],
    "agents": ["agent1", "agent2"],
    "hooks": ["hooks.json"],
    "mcp": ["mcp.json"]
  },
  "exclude": {
    "commands": [],
    "agents": [],
    "hooks": [],
    "mcp": []
  },
  "apply": [
    {
      "project_file_path": "应用到的路径",
      "content": {
        "commands": [],
        "agents": [],
        "hooks": [],
        "mcp": []
      },
      "exclude_content": {
        "commands": [],
        "agents": [],
        "hooks": [],
        "mcp": []
      },
      "hooks_mode": "smart/replace/skip",
      "applied_at": "ISO 8601 时间戳",
      "version": "应用的版本"
    }
  ],
  "metadata": {
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "file_count": 5
  }
}
```

## 配置文件格式要求

### Commands

Command 文件是 Markdown 格式，文件名为 `命令名.md`。

示例：
```markdown
---
name: my-command
description: 我的命令
---

命令说明...
```

### Agents

Agent 文件是 Markdown 格式，必须包含 frontmatter。

示例：
```markdown
---
name: my-agent
description: 我的 Agent
---

Agent 说明...
```

### Hooks

Hooks 是 JSON 格式，定义 hook 事件和对应的处理。

示例：
```json
{
  "tool_use_post": [
    {
      "type": "tool_use",
      "tool_name": "Bash",
      "when": "after",
      "description": "Run after Bash tool"
    }
  ]
}
```

### MCP

MCP 是 JSON 格式，定义 MCP 服务器配置。

示例：
```json
{
  "mcpServers": {
    "server-name": {
      "command": "server-command",
      "args": ["arg1", "arg2"]
    }
  }
}
```

## 命名规范

- 插件名称：小写字母、数字、连字符（kebab-case）
- 文件名：小写字母、数字、下划线（snake_case）
- 版本号：语义化版本（Semantic Versioning）`major.minor.patch`

## Hooks 合并策略说明

### Smart 模式（默认）

Smart 模式智能合并 hooks，保留用户自定义配置。

策略：
1. 对于已存在的 hook 事件，保留用户现有的 hooks
2. 只添加插件中新增的 hook 配置
3. 如果同一事件下有完全相同的命令，跳过

示例：

现有 hooks.json：
```json
{
  "tool_use_post": [
    {
      "type": "tool_use",
      "tool_name": "Read",
      "when": "after",
      "description": "记录 Read 操作"
    }
  ]
}
```

插件的 hooks.json：
```json
{
  "tool_use_post": [
    {
      "type": "tool_use",
      "tool_name": "Bash",
      "when": "after",
      "description": "记录 Bash 操作"
    }
  ]
}
```

合并结果（Smart 模式）：
```json
{
  "tool_use_post": [
    {
      "type": "tool_use",
      "tool_name": "Read",
      "when": "after",
      "description": "记录 Read 操作"
    },
    {
      "type": "tool_use",
      "tool_name": "Bash",
      "when": "after",
      "description": "记录 Bash 操作"
    }
  ]
}
```

### Replace 模式

完全覆盖目标 hooks.json。

### Skip 模式

不处理 hooks，保留现有配置不变。
