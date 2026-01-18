#!/usr/bin/env python3
"""
验证插件脚本
验证插件格式、目录结构和配置文件
"""
import argparse
import sys
from pathlib import Path

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from config_utils import (
    read_share_plugins_json, validate_share_plugins_json,
    validate_version, count_files
)
from file_utils import parse_frontmatter, load_json


def validate_plugin_structure(plugin_path: Path) -> list:
    """
    验证插件目录结构

    Args:
        plugin_path: 插件路径

    Returns:
        错误列表
    """
    errors = []

    if not plugin_path.exists():
        errors.append(f"插件目录不存在: {plugin_path}")
        return errors

    if not plugin_path.is_dir():
        errors.append(f"插件路径不是目录: {plugin_path}")
        return errors

    # 检查必需文件
    required_files = ["share_plugins.json"]
    for file_name in required_files:
        file_path = plugin_path / file_name
        if not file_path.exists():
            errors.append(f"缺少必需文件: {file_name}")

    return errors


def validate_share_json(plugin_path: Path, strict: bool = False) -> list:
    """
    验证 share_plugins.json

    Args:
        plugin_path: 插件路径
        strict: 是否严格模式

    Returns:
        错误列表
    """
    json_file = plugin_path / "share_plugins.json"

    if not json_file.exists():
        return [f"share_plugins.json 不存在"]

    data = read_share_plugins_json(json_file)

    if not data:
        return ["无法读取 share_plugins.json"]

    errors = validate_share_plugins_json(data, strict)

    return errors


def validate_content_files(plugin_path: Path) -> list:
    """
    验证内容文件

    Args:
        plugin_path: 插件路径

    Returns:
        错误列表
    """
    errors = []

    json_file = plugin_path / "share_plugins.json"
    data = read_share_plugins_json(json_file)

    if not data:
        return ["无法读取 share_plugins.json"]

    content = data.get("content", {})

    # 验证 commands
    commands = content.get("commands", [])
    if commands:
        commands_dir = plugin_path / "commands"
        if commands == ["all"]:
            if not commands_dir.exists():
                errors.append("commands 目录不存在（content.commands = 'all'）")
            else:
                # 检查是否有 .md 文件
                md_files = list(commands_dir.glob("*.md"))
                if not md_files:
                    errors.append("commands 目录为空（content.commands = 'all'）")
        else:
            for cmd in commands:
                cmd_file = commands_dir / f"{cmd}.md"
                if not cmd_file.exists():
                    errors.append(f"command 文件不存在: {cmd_file}")

    # 验证 agents
    agents = content.get("agents", [])
    if agents:
        agents_dir = plugin_path / "agents"
        for agent in agents:
            agent_file = agents_dir / f"{agent}.md"
            if not agent_file.exists():
                errors.append(f"agent 文件不存在: {agent_file}")

    # 验证 hooks
    if content.get("hooks"):
        hooks_file = plugin_path / "hooks.json"
        if not hooks_file.exists():
            errors.append("hooks.json 不存在（content.hooks 不为空）")
        else:
            # 验证 JSON 格式
            hooks_data = load_json(hooks_file)
            if not hooks_data:
                errors.append("hooks.json 格式无效")

    # 验证 mcp
    if content.get("mcp"):
        mcp_file = plugin_path / "mcp.json"
        if not mcp_file.exists():
            errors.append("mcp.json 不存在（content.mcp 不为空）")
        else:
            # 验证 JSON 格式
            mcp_data = load_json(mcp_file)
            if not mcp_data:
                errors.append("mcp.json 格式无效")

    return errors


def validate_agent_frontmatter(plugin_path: Path) -> list:
    """
    验证 agent 文件的 frontmatter

    Args:
        plugin_path: 插件路径

    Returns:
        错误列表
    """
    errors = []

    json_file = plugin_path / "share_plugins.json"
    data = read_share_plugins_json(json_file)

    if not data:
        return []

    agents = data.get("content", {}).get("agents", [])
    if not agents:
        return []

    agents_dir = plugin_path / "agents"

    for agent_name in agents:
        agent_file = agents_dir / f"{agent_name}.md"

        if not agent_file.exists():
            continue

        try:
            content = agent_file.read_text(encoding="utf-8")
            frontmatter = parse_frontmatter(content)

            if not frontmatter:
                errors.append(f"agent 文件缺少 frontmatter: {agent_name}")
            else:
                # 检查必需字段
                required_fields = ["name", "description"]
                for field in required_fields:
                    if field not in frontmatter:
                        errors.append(f"agent {agent_name} frontmatter 缺少字段: {field}")

        except Exception as e:
            errors.append(f"读取 agent 文件失败: {agent_name} - {e}")

    return errors


def validate_plugin(plugin_path: Path, strict: bool = False) -> dict:
    """
    验证插件

    Args:
        plugin_path: 插件路径
        strict: 是否严格模式

    Returns:
        验证结果
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": []
    }

    # 验证目录结构
    structure_errors = validate_plugin_structure(plugin_path)
    result["errors"].extend(structure_errors)

    # 验证 share_plugins.json
    json_errors = validate_share_json(plugin_path, strict)
    result["errors"].extend(json_errors)

    # 验证内容文件
    content_errors = validate_content_files(plugin_path)
    result["errors"].extend(content_errors)

    # 验证 agent frontmatter
    agent_errors = validate_agent_frontmatter(plugin_path)
    result["errors"].extend(agent_errors)

    # 检查是否有错误
    result["valid"] = len(result["errors"]) == 0

    return result


def print_validation_result(result: dict) -> None:
    """
    打印验证结果

    Args:
        result: 验证结果
    """
    if result["valid"]:
        print("✓ 验证通过")
    else:
        print("✗ 验证失败")

    if result["errors"]:
        print("\n错误:")
        for error in result["errors"]:
            print(f"  - {error}")

    if result["warnings"]:
        print("\n警告:")
        for warning in result["warnings"]:
            print(f"  - {warning}")


def fix_plugin(plugin_path: Path) -> bool:
    """
    尝试自动修复插件

    Args:
        plugin_path: 插件路径

    Returns:
        是否修复成功
    """
    print("尝试自动修复...")

    json_file = plugin_path / "share_plugins.json"
    data = read_share_plugins_json(json_file)

    if not data:
        print("无法读取 share_plugins.json")
        return False

    fixed = False

    # 修复版本号格式
    if "version" in data:
        version = data["version"]
        if not validate_version(version):
            print(f"修复版本号: {version} -> 1.0.0")
            data["version"] = "1.0.0"
            fixed = True

    # 确保必需字段存在
    required_fields = ["plugin", "version", "content", "metadata"]
    for field in required_fields:
        if field not in data:
            print(f"添加缺失字段: {field}")
            if field == "content":
                data[field] = {"commands": [], "agents": [], "hooks": [], "mcp": []}
            elif field == "metadata":
                data[field] = {"created_at": "", "updated_at": "", "file_count": 0}
            else:
                data[field] = ""
            fixed = True

    # 确保子字段存在
    if "content" in data:
        content_types = ["commands", "agents", "hooks", "mcp"]
        for ct in content_types:
            if ct not in data["content"]:
                print(f"添加 content.{ct}")
                data["content"][ct] = []
                fixed = True

    # 保存
    if fixed:
        from config_utils import write_share_plugins_json
        write_share_plugins_json(json_file, data)
        print("修复完成")
        return True
    else:
        print("无需修复")
        return True


def main():
    parser = argparse.ArgumentParser(description="验证插件")
    parser.add_argument("--plugin", type=str, required=True,
                        help="插件路径")
    parser.add_argument("--strict", action="store_true",
                        help="严格模式")
    parser.add_argument("--fix", action="store_true",
                        help="尝试自动修复")

    args = parser.parse_args()

    plugin_path = Path(args.plugin).expanduser()

    if args.fix:
        # 先尝试修复
        if not fix_plugin(plugin_path):
            return 1

    # 验证插件
    result = validate_plugin(plugin_path, args.strict)

    print_validation_result(result)

    return 0 if result["valid"] else 1


if __name__ == "__main__":
    sys.exit(main())
