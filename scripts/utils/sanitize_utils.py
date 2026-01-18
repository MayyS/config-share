"""
敏感信息脱敏工具模块
用于检测和脱敏 JSON 配置文件中的敏感信息（API keys、tokens 等）
"""
import re
import copy
from typing import Dict, Any, Set, List
from pathlib import Path


# 敏感字段名匹配模式
SENSITIVE_PATTERNS = [
    r'.*_KEY$',
    r'.*_TOKEN$',
    r'.*_SECRET$',
    r'.*_PASSWORD$',
    r'.*_CREDENTIAL$',
    r'.*_APIKEY$',
    r'.*_APITOKEN$',
    r'^apikey$',
    r'^apitoken$',
    r'^api_key$',
    r'^api_token$',
    r'^secret$',
    r'^password$',
    r'^passwd$',
    r'^auth$',
    r'^authentication$',
    r'^credential$',
]

# 编译正则表达式
COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]


def is_sensitive_key(key: str) -> bool:
    """
    判断字段名是否敏感

    Args:
        key: 字段名

    Returns:
        是否为敏感字段
    """
    if not isinstance(key, str):
        return False

    for pattern in COMPILED_PATTERNS:
        if pattern.match(key):
            return True
    return False


def detect_sensitive_fields(data: Any, path: str = "") -> Dict[str, Any]:
    """
    递归检测 JSON 数据中的敏感字段

    Args:
        data: JSON 数据
        path: 当前路径（用于错误信息）

    Returns:
        {字段路径: 原始值} 的字典
    """
    env_vars = {}

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key

            if is_sensitive_key(key) and isinstance(value, str):
                # 记录敏感值
                env_vars[key] = value
            elif isinstance(value, (dict, list)):
                # 递归检查嵌套结构
                nested = detect_sensitive_fields(value, current_path)
                env_vars.update(nested)

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            current_path = f"{path}[{idx}]" if path else f"[{idx}]"
            if isinstance(item, (dict, list)):
                nested = detect_sensitive_fields(item, current_path)
                env_vars.update(nested)

    return env_vars


def sanitize_json(data: Any, env_vars: Dict[str, str]) -> Any:
    """
    将敏感值替换为环境变量占位符

    Args:
        data: 原始 JSON 数据
        env_vars: 敏感字段名到原始值的映射

    Returns:
        处理后的 JSON 数据
    """
    data = copy.deepcopy(data)
    return _sanitize_recursive(data, env_vars)


def _sanitize_recursive(data: Any, env_vars: Dict[str, str]) -> Any:
    """
    递归处理敏感字段

    Args:
        data: 当前数据
        env_vars: 敏感字段映射

    Returns:
        处理后的数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if is_sensitive_key(key) and isinstance(value, str):
                # 替换为占位符
                result[key] = f"${{{key}}}"
            elif isinstance(value, (dict, list)):
                result[key] = _sanitize_recursive(value, env_vars)
            else:
                result[key] = value
        return result

    elif isinstance(data, list):
        return [_sanitize_recursive(item, env_vars) for item in data]

    return data


def generate_env_example(env_vars: Dict[str, str]) -> str:
    """
    生成 .env.example 文件内容

    Args:
        env_vars: 敏感字段名到原始值的映射

    Returns:
        .env.example 文件内容
    """
    lines = ["# 敏感信息配置文件", "# 复制此文件为 .env 并填入真实值", ""]

    for key, value in env_vars.items():
        # 生成占位符说明
        if isinstance(value, str):
            # 根据值类型生成说明
            if len(value) > 0:
                placeholder = f"your-{key.lower()}-here"
                lines.append(f"{key}={placeholder}")
            else:
                lines.append(f"{key}=")

    lines.append("")
    return "\n".join(lines)


def find_env_files(plugin_dir: Path) -> List[Path]:
    """
    查找插件目录中的环境变量相关文件

    Args:
        plugin_dir: 插件目录路径

    Returns:
        找到的文件列表
    """
    env_files = []

    # 查找 .env.example
    env_example = plugin_dir / ".env.example"
    if env_example.exists():
        env_files.append(env_example)

    # 查找 .env（不应该被提交，但可能存在）
    env_file = plugin_dir / ".env"
    if env_file.exists():
        env_files.append(env_file)

    return env_files


def parse_env_example(file_path: Path) -> Dict[str, str]:
    """
    解析 .env.example 文件

    Args:
        file_path: .env.example 文件路径

    Returns:
        环境变量名到说明的字典
    """
    if not file_path.exists():
        return {}

    env_vars = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            # 跳过注释和空行
            if not line or line.startswith("#"):
                continue

            # 解析键值对
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def restore_env_values(data: Any, env_values: Dict[str, str]) -> Any:
    """
    将环境变量占位符恢复为实际值

    Args:
        data: 包含占位符的 JSON 数据
        env_values: 环境变量名到值的映射

    Returns:
        填充了实际值的 JSON 数据
    """
    data = copy.deepcopy(data)
    return _restore_recursive(data, env_values)


def _restore_recursive(data: Any, env_values: Dict[str, str]) -> Any:
    """
    递归恢复环境变量占位符

    Args:
        data: 当前数据
        env_values: 环境变量映射

    Returns:
        恢复后的数据
    """
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_key = value[2:-1]
                if env_key in env_values:
                    result[key] = env_values[env_key]
                else:
                    result[key] = value
            elif isinstance(value, (dict, list)):
                result[key] = _restore_recursive(value, env_values)
            else:
                result[key] = value
        return result

    elif isinstance(data, list):
        return [_restore_recursive(item, env_values) for item in data]

    return data


def count_placeholders(data: Any) -> int:
    """
    统计数据中的环境变量占位符数量

    Args:
        data: JSON 数据

    Returns:
        占位符数量
    """
    count = 0

    if isinstance(data, dict):
        for value in data.values():
            count += count_placeholders(value)
    elif isinstance(data, list):
        for item in data:
            count += count_placeholders(item)
    elif isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        count += 1

    return count
