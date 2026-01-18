# 敏感信息保护机制

## 概述

Config Share Skill 提供自动化的敏感信息保护机制，确保在打包和分享插件时，API keys、tokens、passwords 等敏感信息不会被意外泄露。

## 核心机制

### 敏感字段检测

打包时自动检测以下敏感字段：

| 模式 | 示例 |
|------|------|
| `*_KEY` | `API_KEY`, `OPENAI_KEY` |
| `*_TOKEN` | `AUTH_TOKEN`, `ACCESS_TOKEN` |
| `*_SECRET` | `CLIENT_SECRET`, `WEBHOOK_SECRET` |
| `*_PASSWORD` | `DB_PASSWORD`, `USER_PASSWORD` |
| `*_CREDENTIAL` | `AWS_CREDENTIAL` |
| `apikey` / `api_key` | 各种变体 |
| `apitoken` / `api_token` | 各种变体 |
| `secret` | 独立使用 |
| `password` / `passwd` | 独立使用 |
| `auth` | 独立使用 |

### 占位符替换

检测到的敏感值会被替换为环境变量占位符：

**原始配置**：
```json
{
  "mcpServers": {
    "openai": {
      "env": {
        "OPENAI_API_KEY": "sk-1234567890"
      }
    }
  }
}
```

**打包后配置**：
```json
{
  "mcpServers": {
    "openai": {
      "env": {
        "OPENAI_API_KEY": "${OPENAI_API_KEY}"
      }
    }
  }
}
```

## 使用方法

### 打包插件

默认情况下，敏感信息会自动脱敏：

```bash
python scripts/pack_plugin.py \
  --name my-plugin \
  --mcp \
  --hooks
```

打包后会生成 `.env.example` 文件：

```bash
# 敏感信息配置文件
# 复制此文件为 .env 并填入真实值

OPENAI_API_KEY=your-openai-api-key-here
```

### 跳过脱敏

如果需要保留原始值（不推荐）：

```bash
python scripts/pack_plugin.py \
  --name my-plugin \
  --mcp \
  --skip-sanitize
```

**注意**：使用 `--skip-sanitize` 可能导致敏感信息泄露到公开仓库。

### 应用插件

应用带有敏感信息的插件时，系统会自动提示配置环境变量：

```bash
python scripts/apply_plugin.py \
  --source https://github.com/user/plugin-repo \
  --apply
```

输出示例：

```
============================================================
环境变量配置提示
============================================================
检测到 2 个环境变量需要配置:
  - OPENAI_API_KEY
  - DATABASE_URL

配置步骤:
  1. 复制示例文件: cp ./claude_share/my-plugin/.env.example .env
  2. 编辑 .env 文件，填入真实的环境变量值
  3. 确保环境变量在运行时可访问（通过 export 或 dotenv）
  4. 配置文件中包含 2 个环境变量占位符 (${VAR_NAME})
============================================================
```

## 环境变量配置

### 方法 1：系统环境变量

在 shell 配置文件中设置：

```bash
# ~/.bashrc 或 ~/.zshrc
export OPENAI_API_KEY=your-actual-key
export DATABASE_URL=your-database-url
```

### 方法 2：项目 .env 文件

在项目根目录创建 `.env` 文件：

```bash
# .env
OPENAI_API_KEY=your-actual-key
DATABASE_URL=postgresql://user:pass@localhost/db
```

**注意**：`.env` 文件应添加到 `.gitignore`，避免提交到版本控制。

### 方法 3：运行时加载

使用 `python-dotenv` 或类似工具：

```python
from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件
```

## 安全最佳实践

### 1. 永远不要提交 .env 文件

```gitignore
# .gitignore
.env
.env.local
.env.*.local
```

### 2. 使用环境变量而非硬编码

**不推荐**：
```json
{
  "apiKey": "sk-1234567890"
}
```

**推荐**：
```json
{
  "apiKey": "${API_KEY}"
}
```

### 3. 定期轮换密钥

- API keys 和 access tokens 应定期更新
- 旧的密钥应立即撤销

### 4. 使用最小权限原则

- 只分配必要的权限
- 不同环境使用不同的密钥

### 5. 审计公开仓库

在推送插件仓库前，检查是否包含敏感信息：

```bash
# 搜索可能的敏感信息
grep -r "sk-" .
grep -r "password" .
grep -r "token" .
```

## 故障排除

### 占位符未替换

**症状**：打包后的文件仍包含原始值

**排查步骤**：
1. 检查是否使用了 `--skip-sanitize`
2. 确认字段名匹配敏感模式
3. 使用 `--dry-run` 预览操作

### 环境变量不生效

**症状**：占位符未被替换为实际值

**解决方案**：
1. 确认环境变量已正确设置
2. 检查变量名是否匹配（区分大小写）
3. 确认环境变量加载时机正确

### 占位符格式错误

**正确格式**：`${VARIABLE_NAME}`
**错误格式**：
- `$VARIABLE_NAME` （缺少大括号）
- `{VARIABLE_NAME}` （缺少 $）
- `{{VARIABLE_NAME}}` （双大括号）

## 示例

### 完整的打包流程

```bash
# 1. 打包插件（自动脱敏）
python scripts/pack_plugin.py \
  --name my-mcp-plugin \
  --version 1.0.0 \
  --mcp \
  --hooks \
  --description "My MCP plugin with sensitive config" \
  --author "Your Name"

# 2. 检查生成的 .env.example
cat ./claude_share/my-mcp-plugin/.env.example

# 3. 发布到 GitHub（不包含敏感信息）
cd ./claude_share/my-mcp-plugin
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/username/my-mcp-plugin.git
git push -u origin main
```

### 完整的应用流程

```bash
# 1. 应用插件
python scripts/apply_plugin.py \
  --source https://github.com/username/my-mcp-plugin \
  --apply --mcp --hooks

# 2. 根据提示配置环境变量
cp ./claude_share/my-mcp-plugin/.env.example ~/.claude/.env

# 3. 编辑 .env 文件，填入真实值
vim ~/.claude/.env

# 4. 确保环境变量被加载（取决于你的设置）
# - 如果使用 python-dotenv，确保在代码中调用 load_dotenv()
# - 如果使用系统环境变量，确保 export 或在 shell 配置文件中设置
```

## API 参考

### pack_plugin.py 新增参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `--skip-sanitize` | flag | 跳过敏感信息脱敏（保留原始值） |

### 敏感信息检测 API

在 `sanitize_utils.py` 中提供了以下函数：

```python
# 判断字段名是否敏感
is_sensitive_key(key: str) -> bool

# 检测 JSON 中的敏感字段
detect_sensitive_fields(data: Any, path: str = "") -> Dict[str, Any]

# 替换敏感值为占位符
sanitize_json(data: Any, env_vars: Dict[str, str]) -> Any

# 生成 .env.example 内容
generate_env_example(env_vars: Dict[str, str]) -> str

# 统计占位符数量
count_placeholders(data: Any) -> int
```

## 相关文档

- [plugin-format.md](./plugin-format.md) - 插件格式规范
- [troubleshooting.md](./troubleshooting.md) - 故障排除指南
