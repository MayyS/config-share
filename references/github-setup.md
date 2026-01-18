# GitHub/GitLab 设置指南

## GitHub 设置

### 1. 创建 Personal Access Token

1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token" → "Generate new token (classic)"
3. 设置 Token 名称（如 "config-share"）
4. 选择权限（Scopes）：
   - `repo` - 完整仓库访问权限
   - 或仅 `public_repo` - 仅公开仓库
5. 点击 "Generate token"
6. 复制生成的 Token（只显示一次）

### 2. 设置环境变量

**Linux/macOS:**
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export GITHUB_TOKEN="your_token_here"

# 或临时设置
export GITHUB_TOKEN="your_token_here"
```

**Windows (PowerShell):**
```powershell
# 设置系统环境变量
$env:GITHUB_TOKEN="your_token_here"

# 或永久设置
[System.Environment]::SetEnvironmentVariable('GITHUB_TOKEN', 'your_token_here', 'User')
```

### 3. 创建仓库

**方式 1：自动创建（推荐）**

```bash
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo https://github.com/username/my-plugin \
  --repo-type github \
  --create-repo \
  --token $GITHUB_TOKEN
```

**方式 2：手动创建**

1. 访问 https://github.com/new
2. 填写仓库名称（如 `my-plugin`）
3. 选择 Public 或 Private
4. 不要初始化 README（插件会自己初始化）
5. 点击 "Create repository"

### 4. 发布插件

```bash
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo https://github.com/username/my-plugin \
  --repo-type github \
  --token $GITHUB_TOKEN
```

## GitLab 设置

### 1. 创建 Personal Access Token

1. 访问 https://gitlab.com/-/user_settings/personal_access_tokens
2. 点击 "Add new token"
3. 设置 Token 名称
4. 选择权限：
   - `api`
   - `read_repository`
   - `write_repository`
5. 设置过期时间
6. 点击 "Create personal access token"
7. 复制生成的 Token

### 2. 设置环境变量

**Linux/macOS:**
```bash
export GITLAB_TOKEN="your_token_here"
```

**Windows (PowerShell):**
```powershell
$env:GITLAB_TOKEN="your_token_here"
```

### 3. 创建仓库

GitLab 仓库需要指定项目路径（用户 ID 或组 ID），自动创建功能有限。

**推荐手动创建：**

1. 访问 https://gitlab.com/projects/new
2. 填写项目名称
3. 设置可见性（Public/Private/Internal）
4. 取消 "Initialize repository with a README"
5. 点击 "Create project"

### 4. 发布插件

```bash
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo https://gitlab.com/username/my-plugin \
  --repo-type gitlab \
  --token $GITLAB_TOKEN
```

## 自定义仓库接入

config-share 支持任何 Git 仓库，不限于 GitHub 或 GitLab。

### 1. 准备仓库

确保仓库满足以下条件：
- 可以通过 HTTPS 访问
- 支持推送（需要写权限）
- 支持 Git 标签

### 2. 认证方式

**方式 1：HTTPS 凭证（推荐）**

仓库如果需要认证，使用 `--token` 参数。注意：自定义仓库的 Token 使用方式可能与 GitHub/GitLab 不同。

**方式 2：SSH 密钥**

如果你配置了 SSH 密钥，可以直接使用 SSH URL：

```bash
--repo git@your-server.com:user/repo.git \
--repo-type custom
```

**方式 3：无认证（公开仓库）**

如果仓库是公开且无需认证的：

```bash
--repo https://your-server.com/user/repo.git \
--repo-type custom
```

### 3. 发布到自定义仓库

```bash
python scripts/publish_plugin.py \
  --plugin ./claude_share/my-plugin \
  --repo https://your-server.com/user/repo.git \
  --repo-type custom
```

## SSH/HTTPS 认证配置

### HTTPS 认证

使用 HTTPS 时，Token 会被自动注入到 URL 中。

**优点：**
- 支持通过 `--token` 参数
- 适合 CI/CD 环境

**缺点：**
- 需要每次提供 Token

### SSH 认证

使用 SSH 时，依赖系统的 SSH 密钥配置。

**配置 SSH 密钥：**

```bash
# 生成密钥（如果已有可跳过）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 复制公钥到 GitHub/GitLab
cat ~/.ssh/id_ed25519.pub
```

**优点：**
- 无需每次输入密码
- 更安全

**缺点：**
- 需要 SSH 密钥配置
- config-share 不支持通过 `--token` 注入 SSH 密钥

## 使用说明

### 环境变量优先级

Token 的获取优先级：
1. `--token` 参数
2. 环境变量 `GITHUB_TOKEN` 或 `GITLAB_TOKEN`
3. 无认证（公开仓库）

### 常用命令

**列出已安装的插件：**
```bash
python scripts/list_plugins.py --role user
```

**检查更新：**
```bash
python scripts/update_plugin.py --plugin my-plugin --role user --check-updates
```

**应用更新：**
```bash
python scripts/update_plugin.py --plugin my-plugin --role user --apply
```

**更新插件（分享者）：**
```bash
python scripts/update_plugin.py --plugin my-plugin --role sharer --increment patch --push
```

### 安全建议

1. **不要将 Token 提交到 Git 仓库**
2. **使用 `.env` 文件管理敏感信息**（确保 `.env` 在 `.gitignore` 中）
3. **定期更换 Token**
4. **根据需要设置最小权限**
5. **使用私有仓库存储敏感配置**

## 故障排除

### Token 无效

**错误**：`401 Unauthorized`

**解决方案**：
1. 确认 Token 未过期
2. 确认 Token 有足够权限
3. 重新生成 Token

### 权限不足

**错误**：`403 Forbidden`

**解决方案**：
1. 确认 Token 包含 `repo` 权限（GitHub）
2. 确认你有仓库的推送权限
3. 对于私有仓库，确保 Token 有访问权限

### SSH 连接失败

**错误**：`Permission denied (publickey)`

**解决方案**：
1. 确认 SSH 密钥已添加到账户
2. 测试 SSH 连接：`ssh -T git@github.com`
3. 检查 SSH 配置：`~/.ssh/config`
