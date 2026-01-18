"""
配置处理工具模块
处理 share_plugins.json 的读写和验证
"""
import json
import copy
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import hashlib


DEFAULT_SHARE_PLUGINS_STRUCTURE = {
    "plugin": "",
    "version": "1.0.0",
    "description": "",
    "author": "",
    "license": "MIT",
    "repository": {
        "type": "",
        "url": ""
    },
    "content": {
        "commands": [],
        "agents": [],
        "hooks": [],
        "mcp": []
    },
    "exclude": {
        "commands": [],
        "agents": [],
        "hooks": [],
        "mcp": []
    },
    "apply": [],
    "metadata": {
        "created_at": "",
        "updated_at": "",
        "file_count": 0
    }
}


def read_share_plugins_json(path: Path) -> Optional[Dict[str, Any]]:
    """
    读取 share_plugins.json 文件

    Args:
        path: 文件路径

    Returns:
        解析后的数据，失败返回 None
    """
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"读取 share_plugins.json 失败: {e}")
        return None


def write_share_plugins_json(path: Path, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    写入 share_plugins.json 文件

    Args:
        path: 文件路径
        data: 要写入的数据
        indent: 缩进空格数

    Returns:
        是否成功
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"写入 share_plugins.json 失败: {e}")
        return False


def create_share_plugins_json(plugin_name: str,
                              version: str = "1.0.0",
                              description: str = "",
                              author: str = "",
                              license: str = "MIT") -> Dict[str, Any]:
    """
    创建新的 share_plugins.json 数据结构

    Args:
        plugin_name: 插件名称
        version: 版本号
        description: 描述
        author: 作者
        license: 许可证

    Returns:
        share_plugins.json 数据
    """
    data = copy.deepcopy(DEFAULT_SHARE_PLUGINS_STRUCTURE)
    data["plugin"] = plugin_name
    data["version"] = version
    data["description"] = description
    data["author"] = author
    data["license"] = license
    data["metadata"]["created_at"] = datetime.now().isoformat()
    data["metadata"]["updated_at"] = datetime.now().isoformat()

    return data


def validate_share_plugins_json(data: Dict[str, Any], strict: bool = False) -> List[str]:
    """
    验证 share_plugins.json 格式

    Args:
        data: 要验证的数据
        strict: 是否严格模式

    Returns:
        错误消息列表，空列表表示验证通过
    """
    errors = []

    # 必需字段检查
    required_fields = ["plugin", "version"]
    for field in required_fields:
        if field not in data:
            errors.append(f"缺少必需字段: {field}")
        elif not data[field]:
            errors.append(f"字段为空: {field}")

    # 版本格式检查
    if "version" in data:
        if not validate_version(data["version"]):
            errors.append(f"版本号格式无效: {data['version']}")

    # content 结构检查
    if "content" in data:
        content_types = ["commands", "agents", "hooks", "mcp"]
        for ct in content_types:
            if ct not in data["content"]:
                data["content"][ct] = []
            elif not isinstance(data["content"][ct], list):
                errors.append(f"content.{ct} 必须是列表")

    # 严格模式检查
    if strict:
        strict_fields = list(DEFAULT_SHARE_PLUGINS_STRUCTURE.keys())
        for field in strict_fields:
            if field not in data:
                errors.append(f"严格模式: 缺少字段 {field}")

    return errors


def validate_version(version: str) -> bool:
    """
    验证语义化版本格式

    Args:
        version: 版本字符串

    Returns:
        是否有效
    """
    pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$'
    return bool(pattern.match(version))


def increment_version(version: str, increment_type: str = "patch") -> str:
    """
    递增版本号

    Args:
        version: 当前版本
        increment_type: 递增类型 (patch/minor/major)

    Returns:
        新版本号
    """
    parts = version.split("-")
    version_part = parts[0]

    try:
        major, minor, patch = map(int, version_part.split("."))
    except (ValueError, AttributeError):
        return version

    if increment_type == "patch":
        patch += 1
    elif increment_type == "minor":
        minor += 1
        patch = 0
    elif increment_type == "major":
        major += 1
        minor = 0
        patch = 0

    new_version = f"{major}.{minor}.{patch}"
    if len(parts) > 1:
        new_version += f"-{parts[1]}"

    return new_version


def compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号

    Args:
        v1: 版本1
        v2: 版本2

    Returns:
        -1: v1 < v2
        0: v1 == v2
        1: v1 > v2
    """
    # 移除预发布标识
    v1_clean = v1.split("-")[0]
    v2_clean = v2.split("-")[0]

    try:
        v1_parts = list(map(int, v1_clean.split(".")))
        v2_parts = list(map(int, v2_clean.split(".")))
    except (ValueError, AttributeError):
        return 0

    # 补齐到3位
    v1_parts.extend([0] * (3 - len(v1_parts)))
    v2_parts.extend([0] * (3 - len(v2_parts)))

    for a, b in zip(v1_parts, v2_parts):
        if a < b:
            return -1
        elif a > b:
            return 1

    return 0


def merge_configs(old: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个配置

    Args:
        old: 旧配置
        new: 新配置

    Returns:
        合并后的配置
    """
    merged = copy.deepcopy(old)

    for key, value in new.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        elif key in merged and isinstance(merged[key], list) and isinstance(value, list):
            # 列表需要特殊处理，这里简单追加
            merged[key] = merged[key] + value
        else:
            merged[key] = copy.deepcopy(value)

    return merged


def update_apply_record(plugin_data: Dict[str, Any],
                       target_path: str,
                       content: Dict[str, List[str]],
                       exclude_content: Dict[str, List[str]],
                       hooks_mode: str = "smart") -> Dict[str, Any]:
    """
    更新插件的应用记录

    Args:
        plugin_data: 插件数据
        target_path: 目标路径
        content: 应用内容
        exclude_content: 排除内容
        hooks_mode: hooks 处理模式

    Returns:
        更新后的插件数据
    """
    if "apply" not in plugin_data:
        plugin_data["apply"] = []

    # 移除同一路径的旧记录
    plugin_data["apply"] = [
        record for record in plugin_data["apply"]
        if record.get("project_file_path") != target_path
    ]

    # 添加新记录
    plugin_data["apply"].append({
        "project_file_path": target_path,
        "content": content,
        "exclude_content": exclude_content,
        "hooks_mode": hooks_mode,
        "applied_at": datetime.now().isoformat(),
        "version": plugin_data.get("version", "1.0.0")
    })

    plugin_data["metadata"]["updated_at"] = datetime.now().isoformat()

    return plugin_data


def calculate_file_hash(file_path: Path) -> str:
    """
    计算文件的 SHA256 哈希

    Args:
        file_path: 文件路径

    Returns:
        文件哈希值
    """
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""


def count_files(directory: Path, pattern: str = "**/*") -> int:
    """
    计算目录下的文件数量

    Args:
        directory: 目录路径
        pattern: 匹配模式

    Returns:
        文件数量
    """
    if not directory.exists():
        return 0

    count = 0
    for item in directory.glob(pattern):
        if item.is_file():
            count += 1
    return count


def get_plugin_path(plugin_name: str, share_dir: Path) -> Path:
    """
    获取插件路径

    Args:
        plugin_name: 插件名称
        share_dir: 共享目录

    Returns:
        插件路径
    """
    return share_dir / plugin_name


def list_installed_plugins(share_dir: Path) -> List[Dict[str, Any]]:
    """
    列出已安装的插件

    Args:
        share_dir: 共享目录

    Returns:
        插件信息列表
    """
    plugins = []
    if not share_dir.exists():
        return plugins

    for plugin_dir in share_dir.iterdir():
        if not plugin_dir.is_dir():
            continue

        json_file = plugin_dir / "share_plugins.json"
        if not json_file.exists():
            continue

        data = read_share_plugins_json(json_file)
        if data:
            plugins.append({
                "name": data.get("plugin", plugin_dir.name),
                "path": str(plugin_dir),
                "version": data.get("version", "unknown"),
                "description": data.get("description", ""),
                "author": data.get("author", ""),
                "repository": data.get("repository", {}),
                "created_at": data.get("metadata", {}).get("created_at", ""),
                "updated_at": data.get("metadata", {}).get("updated_at", "")
            })

    return plugins


def find_plugin_by_name(plugin_name: str, share_dir: Path) -> Optional[Dict[str, Any]]:
    """
    根据名称查找插件

    Args:
        plugin_name: 插件名称
        share_dir: 共享目录

    Returns:
        插件信息，未找到返回 None
    """
    for plugin in list_installed_plugins(share_dir):
        if plugin["name"] == plugin_name:
            return plugin
    return None
