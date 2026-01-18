#!/usr/bin/env python3
"""
删除插件脚本
"""
import argparse
import sys
import shutil
from pathlib import Path

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from config_utils import get_plugin_path, get_share_dir, read_share_plugins_json


def get_applied_files(plugin_data: dict) -> list:
    """
    获取插件应用的文件列表

    Args:
        plugin_data: 插件数据

    Returns:
        应用的文件路径列表
    """
    applied_files = []

    # 从 apply 记录中获取
    for record in plugin_data.get("apply", []):
        project_path = Path(record.get("project_file_path", ""))
        content = record.get("content", {})

        # commands
        commands = content.get("commands", [])
        if commands == ["all"]:
            # 无法确定具体文件，返回目录
            applied_files.append(project_path / "commands")
        else:
            for cmd in commands:
                applied_files.append(project_path / "commands" / f"{cmd}.md")

        # agents
        for agent in content.get("agents", []):
            applied_files.append(project_path / "agents" / f"{agent}.md")

        # hooks
        if content.get("hooks"):
            applied_files.append(project_path / "hooks.json")

        # mcp
        if content.get("mcp"):
            applied_files.append(project_path / "mcp.json")

    return applied_files


def remove_plugin(plugin_name: str, confirm: bool = False,
                  keep_cache: bool = False) -> bool:
    """
    删除插件

    Args:
        plugin_name: 插件名称
        confirm: 是否自动确认
        keep_cache: 是否保留缓存

    Returns:
        是否成功
    """
    share_dir = get_share_dir()
    plugin_dir = get_plugin_path(plugin_name, share_dir)

    if not plugin_dir.exists():
        print(f"插件不存在: {plugin_name}")
        return False

    # 读取插件数据
    json_file = plugin_dir / "share_plugins.json"
    plugin_data = read_share_plugins_json(json_file)

    if not plugin_data:
        print(f"无法读取插件数据: {plugin_name}")
        return False

    print(f"删除插件: {plugin_name}")
    print(f"  版本: {plugin_data.get('version', 'unknown')}")
    print(f"  路径: {plugin_dir}")

    # 显示应用的文件
    if plugin_data.get("apply"):
        print("\n应用的文件:")
        for record in plugin_data["apply"]:
            project_path = record.get("project_file_path", "")
            content = record.get("content", {})
            print(f"  目标路径: {project_path}")

            commands = content.get("commands", [])
            if commands == ["all"]:
                print(f"    commands: (all)")
            else:
                print(f"    commands: {', '.join(commands)}")

            agents = content.get("agents", [])
            if agents:
                print(f"    agents: {', '.join(agents)}")

            if content.get("hooks"):
                print(f"    hooks: hooks.json")

            if content.get("mcp"):
                print(f"    mcp: mcp.json")

    # 确认
    if not confirm:
        response = input("\n确认删除？(y/N): ")
        if response.lower() != "y":
            print("已取消")
            return False

    # 删除配置文件
    if plugin_data.get("apply"):
        print("\n删除配置文件...")

        for record in plugin_data["apply"]:
            project_path = Path(record.get("project_file_path", ""))
            content = record.get("content", {})

            # commands
            commands = content.get("commands", [])
            if commands and commands != ["all"]:
                commands_dir = project_path / "commands"
                for cmd in commands:
                    cmd_file = commands_dir / f"{cmd}.md"
                    if cmd_file.exists():
                        try:
                            cmd_file.unlink()
                            print(f"  删除: {cmd_file}")
                        except Exception as e:
                            print(f"  删除失败: {cmd_file} - {e}")

            # agents
            for agent in content.get("agents", []):
                agent_file = project_path / "agents" / f"{agent}.md"
                if agent_file.exists():
                    try:
                        agent_file.unlink()
                        print(f"  删除: {agent_file}")
                    except Exception as e:
                        print(f"  删除失败: {agent_file} - {e}")

            # hooks
            if content.get("hooks"):
                hooks_file = project_path / "hooks.json"
                if hooks_file.exists():
                    try:
                        hooks_file.unlink()
                        print(f"  删除: {hooks_file}")
                    except Exception as e:
                        print(f"  删除失败: {hooks_file} - {e}")

            # mcp
            if content.get("mcp"):
                mcp_file = project_path / "mcp.json"
                if mcp_file.exists():
                    try:
                        mcp_file.unlink()
                        print(f"  删除: {mcp_file}")
                    except Exception as e:
                        print(f"  删除失败: {mcp_file} - {e}")

    # 删除缓存
    if not keep_cache:
        print("\n删除缓存...")
        try:
            shutil.rmtree(plugin_dir)
            print(f"  删除: {plugin_dir}")
        except Exception as e:
            print(f"  删除失败: {plugin_dir} - {e}")
            return False
    else:
        print("\n保留缓存")

    print("\n删除完成")
    return True


def main():
    parser = argparse.ArgumentParser(description="删除插件")
    parser.add_argument("--plugin", type=str, required=True,
                        help="插件名称")
    parser.add_argument("--confirm", action="store_true",
                        help="自动确认，不询问")
    parser.add_argument("--keep-cache", action="store_true",
                        help="保留插件缓存")

    args = parser.parse_args()

    success = remove_plugin(args.plugin, args.confirm, args.keep_cache)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
