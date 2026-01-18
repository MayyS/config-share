---
name: config-share
description: 用于团队协同分享 Claude Code 配置（commands、agents、hooks、mcp、skills），支持打包、发布、应用和更新插件
---

# Config Share 技能

## 交互指令 (Prompt Instructions)

当用户调用 `/config-share` 且未提供具体参数时，**必须**遵循以下交互流程。严禁仅输出文本列表，必须使用 `AskUserQuestion` 工具。

### 1. 主菜单 (Main Menu)
使用 `AskUserQuestion` 展示主菜单：
- **Question**: "Config Share 工具集已加载。请选择您要执行的操作："
- **Options**:
  1. **打包分享 (Pack)** - 将配置打包成插件
  2. **应用插件 (Apply)** - 安装插件
  3. **管理插件 (Manage)** - 查看已安装插件
  4. **验证插件 (Validate)** - 检查插件格式

### 2. 细粒度操作流程 (Detailed Workflows)

#### 📦 用户选择 "Pack" (打包)
1. **询问名称**: 使用 `AskUserQuestion` 询问插件名称 (e.g., "my-team-config")。
2. **扫描资源**: 使用 `bash` 命令扫描当前目录下的资源：
   - Commands: `ls commands/*.md`
   - Agents: `ls agents/*.md`
   - Skills: `ls -d skills/*/`
   - MCP: 检查 `mcp.json` 是否存在
3. **选择内容**: 根据扫描结果，使用 `AskUserQuestion` (multiSelect=true) 让用户勾选要打包的具体内容。
   - **重要**: 选项必须清晰标识类型，例如 `[Agent] code-reviewer`, `[Command] git-commit`, `[Skill] python-expert`。
   - 如果某类资源为空，则不显示该类别的选项。
4. **执行**: 根据用户选择，构建并运行 `pack_plugin.py` 命令。
   - 例如: `python scripts/pack_plugin.py --name my-plugin --agents code-reviewer --commands git-commit`

#### 📥 用户选择 "Apply" (应用)
1. **询问来源**: 使用 `AskUserQuestion` 询问插件来源 (Git URL 或本地路径)。
2. **下载/分析**: 先运行下载命令以获取元数据: `python scripts/apply_plugin.py --source <URL> --download`
3. **扫描下载内容**: 检查下载目录（通常在输出日志中会显示路径，或者默认在临时目录）中的 `share_plugins.json` 或直接扫描目录结构。
4. **选择内容**: 使用 `AskUserQuestion` (multiSelect=true) 列出插件中包含的所有组件，让用户勾选要安装的部分。
   - 选项应包括插件内的所有 agents, commands, skills 等。
5. **执行**: 根据用户选择，构建并运行 `apply_plugin.py` 命令。
   - 例如: `python scripts/apply_plugin.py --source <URL> --apply --agents code-reviewer`

#### 🔧 用户选择 "Manage" (管理)
1. 运行 `python scripts/list_plugins.py` 展示列表。
2. 使用 `AskUserQuestion` 询问后续操作（删除插件、更新插件或退出）。

---

用于团队协同分享 Claude Code 配置（commands、agents、hooks、mcp、skills），支持打包、发布、应用和更新插件。

## 核心概念

- **Sharer（分享者）**: 创建并维护配置插件的用户
- **User（用户）**: 应用和管理已安装的插件
- **Plugin（插件）**: 包含一组配置的打包单元
- **插件存储目录**: `./claude_share/`（当前项目目录下）

## 工作流程决策树

```
用户请求
  │
  ├─ 打包分享？ ──→ [pack_plugin] → [publish_plugin]
  │
  ├─ 应用插件？ ──→ [apply_plugin]
  │
  ├─ 更新插件？ ──→ [update_plugin]
  │     ├─ 我是分享者？ → 更新本地 → [publish_plugin --push-only]
  │     └─ 我是用户？ → [update_plugin --apply]
  │
  ├─ 管理插件？ ──→ [list_plugins]
  │
  └─ 验证插件？ ──→ [validate_plugin]
```

## 分享者工作流

### 1. 打包插件

```bash
# 列出可打包的内容
python scripts/pack_plugin.py --list

# 打包插件（包含 commands、agents、hooks、mcp 和 skills）
python scripts/pack_plugin.py \
  --name my-plugin \
  --version 1.0.0 \
  --commands all \
  --agents agent1,agent2 \
  --hooks \
  --mcp \
  --skills all

# 排除特定文件
python scripts/pack_plugin.py \
  --name my-plugin \
  --commands all \
  --skills skill1,skill2 \
  --exclude '{"commands": ["private-command.md"], "skills": ["private-skill"]}'
```

### 2. 发布到仓库

```bash
# 发布到 GitHub（支持用户自定义仓库）
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo https://github.com/username/my-plugin \
  --repo-type github \
  --token $GITHUB_TOKEN

# 发布到 GitLab
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo https://gitlab.com/username/my-plugin \
  --repo-type gitlab \
  --token $GITLAB_TOKEN

# 发布到自定义仓库（用户自行提供仓库信息）
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo <your-custom-repo-url> \
  --repo-type custom
```

### 3. 更新插件

```bash
# 作为分享者更新插件
python scripts/update_plugin.py \
  --plugin my-plugin \
  --role sharer \
  --source ~/.claude/ \
  --increment patch \
  --push
```

## 用户工作流

### 1. 应用插件

```bash
# 检查冲突
python scripts/apply_plugin.py \
  --source https://github.com/username/my-plugin \
  --check-conflicts

# 应用插件（Hooks 使用 smart 模式，包含 skills）
python scripts/apply_plugin.py \
  --source https://github.com/username/my-plugin \
  --target ~/.claude/ \
  --apply \
  --hooks smart \
  --skills all

# 只应用特定内容
python scripts/apply_plugin.py \
  --source https://github.com/username/my-plugin \
  --commands agent1,agent2 \
  --skills skill1 \
  --hooks replace

# 试运行
python scripts/apply_plugin.py \
  --source https://github.com/username/my-plugin \
  --dry-run
```

### 2. 更新已安装的插件

```bash
# 检查更新
python scripts/update_plugin.py \
  --plugin my-plugin \
  --role user \
  --check-updates

# 应用更新
python scripts/update_plugin.py \
  --plugin my-plugin \
  --role user \
  --apply
```

### 3. 管理插件

```bash
# 列出已安装的插件
python scripts/list_plugins.py --role user

# 显示插件详情
python scripts/list_plugins.py \
  --role user \
  --plugin my-plugin \
  --details

# 列出自己维护的插件
python scripts/list_plugins.py --role sharer

# JSON 格式输出
python scripts/list_plugins.py --format json
```

### 4. 删除插件

```bash
# 删除插件
python scripts/remove_plugin.py \
  --plugin my-plugin \
  --confirm
```

## 验证插件

```bash
# 验证插件格式
python scripts/validate_plugin.py \
  --plugin ./claude_share/my-plugin

# 严格模式验证
python scripts/validate_plugin.py \
  --plugin ./claude_share/my-plugin \
  --strict
```

## 资源引用

- **plugin-format.md**: 插件格式说明 (`references/plugin-format.md`)
- **troubleshooting.md**: 故障排除指南 (`references/troubleshooting.md`)
- **github-setup.md**: GitHub/GitLab 设置指南 (`references/github-setup.md`)
- **security.md**: 敏感信息保护机制 (`references/security.md`)

## 配置文件路径

- 技能目录: `~/.claude/skills/config-share/`
- 脚本目录: `scripts/`（相对于技能目录）
- 插件存储: `./claude_share/`（当前项目目录）
- 默认源路径: `~/.claude/`
- 默认目标路径: `~/.claude/`

## 关键特性

### Hooks 智能合并

- **smart 模式**（默认）: 保留用户自定义的 hooks，只添加新 hooks
- **replace 模式**: 完全覆盖目标 hooks.json
- **skip 模式**: 不处理 hooks

### 文件冲突处理

- **ask**: 询问用户如何处理
- **overwrite**: 覆盖现有文件
- **skip**: 跳过冲突文件
- **rename**: 重命名新文件

### 多仓库支持

- GitHub
- GitLab
- 自定义仓库（用户自行提供）

### 敏感信息保护

打包时自动检测和脱敏敏感信息（API keys、tokens、passwords 等）：

- **自动检测**: 识别以 `_KEY`、`_TOKEN`、`_SECRET`、`_PASSWORD` 结尾的字段
- **占位符替换**: 将敏感值替换为 `${VAR_NAME}` 格式的环境变量占位符
- **.env.example 生成**: 自动生成环境变量模板文件

**使用示例**：

```bash
# 打包时自动脱敏
python scripts/pack_plugin.py \
  --name my-plugin \
  --mcp \
  --hooks

# 跳过脱敏（不推荐）
python scripts/pack_plugin.py \
  --name my-plugin \
  --mcp \
  --skip-sanitize
```

详细说明请参考 `references/security.md`。
