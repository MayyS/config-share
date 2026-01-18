# Config Share

用于团队协同分享 Claude Code 配置（commands、agents、hooks、mcp、skills）的 Skill。

## 功能

- 打包个人配置为可分享的插件
- 发布插件到 GitHub/GitLab/自定义仓库
- 从远程仓库应用插件
- 插件更新和管理
- Hooks 智能合并
- 文件冲突处理
- Skills 目录完整复制

## 安装

将 `config-share` 目录复制到 `~/.claude/skills/`。

## 使用

```bash
# 打包插件
python scripts/pack_plugin.py --name my-plugin --commands all --skills all

# 发布到 GitHub
python scripts/publish_plugin.py --plugin ./claude_share/my-plugin \
  --repo https://github.com/username/my-plugin

# 应用插件
python scripts/apply_plugin.py --source https://github.com/username/my-plugin --apply --skills all
```

## 文档

- [插件格式说明](references/plugin-format.md)
- [故障排除](references/troubleshooting.md)
- [GitHub/GitLab 设置](references/github-setup.md)

## 许可证

MIT License
