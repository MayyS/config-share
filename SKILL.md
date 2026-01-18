---
name: config-share
description: 用于团队协同分享 Claude Code 配置（commands、agents、hooks、mcp），支持打包、发布、应用和更新插件
---

# Config Share 技能

用于团队协同分享 Claude Code 配置（commands、agents、hooks、mcp），支持打包、发布、应用和更新插件。

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

# 打包插件（包含 commands 和 agents）
python scripts/pack_plugin.py \
  --name my-plugin \
  --version 1.0.0 \
  --commands all \
  --agents agent1,agent2 \
  --hooks \
  --mcp

# 排除特定文件
python scripts/pack_plugin.py \
  --name my-plugin \
  --commands all \
  --exclude '{"commands": ["private-command.md"]}'
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

# 应用插件（Hooks 使用 smart 模式）
python scripts/apply_plugin.py \
  --source https://github.com/username/my-plugin \
  --target ~/.claude/ \
  --apply \
  --hooks smart

# 只应用特定内容
python scripts/apply_plugin.py \
  --source https://github.com/username/my-plugin \
  --commands agent1,agent2 \
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
