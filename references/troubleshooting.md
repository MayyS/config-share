# 故障排除指南

## 常见错误及解决方案

### 插件目录不存在

**错误信息**：
```
插件目录不存在: ./claude_share/my-plugin
```

**解决方案**：
1. 检查插件名称是否正确
2. 确认插件是否已正确安装
3. 使用 `list_plugins.py` 查看已安装的插件

### share_plugins.json 不存在或无效

**错误信息**：
```
错误: share_plugins.json 不存在
share_plugins.json 验证失败
```

**解决方案**：
1. 使用 `validate_plugin.py` 验证插件格式
2. 如果需要，使用 `--fix` 参数尝试自动修复
3. 检查 JSON 格式是否正确

### 无法克隆仓库

**错误信息**：
```
克隆仓库失败
fatal: repository 'xxx' not found
```

**解决方案**：
1. 检查仓库 URL 是否正确
2. 确认仓库是否为公开或已设置正确的 Token
3. 检查网络连接
4. 使用 HTTPS 而非 SSH（Token 只支持 HTTPS）

### 认证失败

**错误信息**：
```
fatal: Authentication failed
Git push 失败
```

**解决方案**：
1. 设置环境变量：
   ```bash
   export GITHUB_TOKEN=your_token_here  # GitHub
   export GITLAB_TOKEN=your_token_here   # GitLab
   ```
2. 或使用 `--token` 参数
3. 确认 Token 权限足够

### 文件冲突

**错误信息**：
```
发现 2 个冲突:
  [COMMAND] my-command
  [AGENT] my-agent
```

**解决方案**：
1. 使用 `--conflict-mode` 指定处理方式：
   - `ask`: 询问如何处理（默认）
   - `overwrite`: 覆盖现有文件
   - `skip`: 跳过冲突文件
   - `rename`: 重命名新文件

### Hooks 合并问题

**问题描述**：
应用插件后 hooks 未按预期合并

**解决方案**：
1. 检查 `--hooks` 模式是否正确：
   - `smart`: 智能合并（推荐）
   - `replace`: 完全覆盖
   - `skip`: 跳过
2. 手动检查合并后的 `~/.claude/hooks.json`
3. 如需回滚，删除插件并重新应用

## 网络问题

### 连接超时

**错误信息**：
```
requests.exceptions.Timeout
```

**解决方案**：
1. 检查网络连接
2. 尝试使用代理
3. 下载插件到本地后使用本地路径应用

### 无法访问仓库

**错误信息**：
```
requests.exceptions.ConnectionError
```

**解决方案**：
1. 确认仓库 URL 可访问
2. 检查防火墙设置
3. 使用本地克隆的仓库

## Git 操作失败

### 推送失败

**错误信息**：
```
Git push 失败: failed to push some refs
```

**解决方案**：
1. 先拉取远程更新：
   ```bash
   cd ./claude_share/my-plugin
   git pull origin main
   ```
2. 解决冲突后再推送
3. 或使用 `git push --force-with-lease`（慎用）

### 标签推送失败

**错误信息**：
```
推送标签失败
```

**解决方案**：
1. 检查标签是否已存在
2. 手动删除远程标签：
   ```bash
   git push origin :refs/tags/v1.0.0
   ```
3. 重新推送标签

## 文件冲突处理

### 如何处理同名文件

当插件中包含与现有文件同名的文件时：

**方案 1：跳过**
```bash
python scripts/apply_plugin.py --source URL --conflict-mode skip
```

**方案 2：重命名**
```bash
python scripts/apply_plugin.py --source URL --conflict-mode rename
```
新文件会被重命名为 `文件名_1.md`、`文件名_2.md` 等

**方案 3：覆盖**
```bash
python scripts/apply_plugin.py --source URL --conflict-mode overwrite
```
会覆盖现有文件（谨慎使用）

### 手动解决冲突

如果自动解决冲突不符合预期：

1. 使用 `--check-conflicts` 预先检查
2. 应用时选择 `--conflict-mode rename`
3. 手动合并文件内容
4. 删除不需要的文件

## Hooks 合并问题

### Smart 模式不生效

**症状**：应用插件后 hooks 没有合并

**排查步骤**：
1. 确认使用了 `--hooks smart`（默认）
2. 检查插件的 hooks.json 格式是否正确
3. 检查现有的 ~/.claude/hooks.json 格式
4. 使用 `validate_plugin.py` 验证插件

### 完全覆盖 hooks

如果需要完全覆盖现有 hooks：

```bash
python scripts/apply_plugin.py --source URL --hooks replace
```

## 版本管理问题

### 版本号格式错误

**错误信息**：
```
版本号格式无效: 1.0
```

**解决方案**：
1. 使用语义化版本：`major.minor.patch`
2. 例如：`1.0.0`、`1.2.3`、`2.0.0`
3. 支持预发布标签：`1.0.0-beta.1`

### 更新检查失败

**症状**：`--check-updates` 无法获取远程版本

**解决方案**：
1. 确认插件已关联仓库
2. 检查 share_plugins.json 中的 repository 字段
3. 确认远程仓库有版本标签

## 其他问题

### Python 模块缺失

**错误信息**：
```
ModuleNotFoundError: No module named 'requests'
```

**解决方案**：
```bash
pip install requests pyyaml
```

### 权限错误

**错误信息**：
```
PermissionError: [Errno 13] Permission denied
```

**解决方案**：
1. 确保对目标目录有写入权限
2. 使用 `sudo`（不推荐）或更改目录权限
3. 检查文件是否被其他进程锁定

### 大文件处理

**症状**：处理大量 commands/agents 时速度慢

**解决方案**：
1. 使用 `--list` 先查看可打包内容
2. 只打包需要的文件：
   ```bash
   --commands cmd1,cmd2
   --agents agent1,agent2
   ```
3. 使用 `--exclude` 排除不需要的文件

## 获取帮助

如果以上解决方案无法解决问题：

1. 检查所有脚本的 `--help` 参数
2. 使用 `--dry-run` 预览操作
3. 使用 `validate_plugin.py` 验证插件
4. 查看参考文档：
   - `plugin-format.md`: 插件格式
   - `github-setup.md`: GitHub/GitLab 设置
