#!/usr/bin/env python3
"""
列出/管理插件脚本
"""
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from config_utils import list_installed_plugins, get_share_dir, find_plugin_by_name
from git_utils import get_remotes


def format_plugins_table(plugins: list) -> str:
    """
    格式化插件为表格

    Args:
        plugins: 插件列表

    Returns:
        格式化后的表格字符串
    """
    if not plugins:
        return "暂无插件"

    # 计算列宽
    name_width = max(15, max(len(p["name"]) for p in plugins))
    version_width = 10
    author_width = max(10, max(len(p["author"]) for p in plugins))
    desc_width = max(30, max(len(p["description"][:30]) for p in plugins))

    # 表头
    header = f"{'名称'.ljust(name_width)} {'版本'.ljust(version_width)} {'作者'.ljust(author_width)} {'描述'.ljust(desc_width)} {'更新时间'}"
    separator = "-" * (name_width + version_width + author_width + desc_width + 20)

    result = [header, separator]

    for plugin in plugins:
        name = plugin["name"]
        version = plugin["version"]
        author = plugin["author"] or "-"
        description = (plugin["description"] or "-")[:desc_width]
        updated_at = plugin["updated_at"]

        # 格式化时间
        if updated_at:
            try:
                dt = datetime.fromisoformat(updated_at)
                updated_at = dt.strftime("%Y-%m-%d")
            except:
                updated_at = "-"
        else:
            updated_at = "-"

        row = f"{name.ljust(name_width)} {version.ljust(version_width)} {author.ljust(author_width)} {description.ljust(desc_width)} {updated_at}"
        result.append(row)

    return "\n".join(result)


def format_plugins_compact(plugins: list) -> str:
    """
    格式化插件为紧凑列表

    Args:
        plugins: 插件列表

    Returns:
        格式化后的紧凑列表字符串
    """
    if not plugins:
        return "暂无插件"

    result = []
    for i, plugin in enumerate(plugins, 1):
        result.append(f"{i}. {plugin['name']} (v{plugin['version']})")
        if plugin["description"]:
            result.append(f"   {plugin['description']}")
        if plugin["author"]:
            result.append(f"   作者: {plugin['author']}")

    return "\n".join(result)


def format_plugins_json(plugins: list) -> str:
    """
    格式化插件为 JSON

    Args:
        plugins: 插件列表

    Returns:
        JSON 字符串
    """
    return json.dumps(plugins, indent=2, ensure_ascii=False)


def show_plugin_details(plugin_name: str, share_dir: Path) -> bool:
    """
    显示插件详情

    Args:
        plugin_name: 插件名称
        share_dir: 共享目录

    Returns:
        是否成功
    """
    plugin = find_plugin_by_name(plugin_name, share_dir)

    if not plugin:
        print(f"插件未找到: {plugin_name}")
        return False

    print(f"插件: {plugin['name']}")
    print(f"路径: {plugin['path']}")
    print(f"版本: {plugin['version']}")
    print(f"作者: {plugin['author'] or '-'}")
    print(f"描述: {plugin['description'] or '-'}")
    print(f"更新时间: {plugin['updated_at'] or '-'}")

    # 仓库信息
    if plugin.get("repository"):
        repo = plugin["repository"]
        print(f"仓库类型: {repo.get('type', '-')}")
        print(f"仓库 URL: {repo.get('url', '-')}")

    # Git 仓库信息
    plugin_path = Path(plugin["path"])
    if (plugin_path / ".git").exists():
        print(f"Git 仓库: 是")
        remotes = get_remotes(plugin_path)
        if remotes:
            print(f"远程仓库:")
            for name, url in remotes.items():
                print(f"  {name}: {url}")
    else:
        print(f"Git 仓库: 否")

    return True


def list_plugins(role: str = "user", plugin_name: str = None,
                details: bool = False, format_type: str = "table") -> int:
    """
    列出插件

    Args:
        role: 角色
        plugin_name: 插件名称（显示详情）
        details: 是否显示详情
        format_type: 输出格式

    Returns:
        退出码
    """
    share_dir = get_share_dir()

    if not share_dir.exists():
        print(f"插件目录不存在: {share_dir}")
        return 0

    plugins = list_installed_plugins(share_dir)

    if not plugins:
        print("暂无已安装的插件")
        return 0

    # 过滤特定插件
    if plugin_name:
        if details:
            if show_plugin_details(plugin_name, share_dir):
                return 0
            else:
                return 1
        else:
            plugins = [p for p in plugins if p["name"] == plugin_name]
            if not plugins:
                print(f"插件未找到: {plugin_name}")
                return 1

    # 过滤角色
    # sharer: 有仓库信息的插件
    # user: 所有已安装的插件
    if role == "sharer":
        plugins = [p for p in plugins if p.get("repository", {}).get("url")]
        if not plugins:
            print("没有维护中的插件（没有关联仓库的插件）")
            return 0

    print(f"角色: {role}")
    print(f"插件数量: {len(plugins)}")
    print()

    # 输出
    if format_type == "json":
        print(format_plugins_json(plugins))
    elif format_type == "compact":
        print(format_plugins_compact(plugins))
    else:  # table
        print(format_plugins_table(plugins))

    return 0


def main():
    parser = argparse.ArgumentParser(description="列出插件")
    parser.add_argument("--role", type=str, default="user",
                        choices=["user", "sharer"],
                        help="角色，默认 user")
    parser.add_argument("--plugin", type=str, default="",
                        help="插件名称")
    parser.add_argument("--details", action="store_true",
                        help="显示详情")
    parser.add_argument("--format", type=str, default="table",
                        choices=["table", "json", "compact"],
                        help="输出格式，默认 table")

    args = parser.parse_args()

    return list_plugins(
        args.role,
        args.plugin or None,
        args.details,
        args.format
    )


if __name__ == "__main__":
    sys.exit(main())
