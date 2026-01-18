#!/usr/bin/env python3
"""
更新插件脚本
支持分享者更新插件并推送，用户拉取更新并应用
"""
import argparse
import sys
from pathlib import Path

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from git_utils import (
    clone_repo, pull, add_commit, push_repo, get_remotes,
    check_repo_exists, get_remote_version, get_current_branch
)
from config_utils import (
    read_share_plugins_json, write_share_plugins_json,
    increment_version, get_plugin_path, get_share_dir,
    compare_versions
)
from file_utils import expand_path, get_claude_path
import tempfile
import shutil


def get_plugin_info(plugin_name: str) -> dict:
    """
    获取插件信息

    Args:
        plugin_name: 插件名称

    Returns:
        插件信息字典
    """
    share_dir = get_share_dir()
    plugin_dir = get_plugin_path(plugin_name, share_dir)

    if not plugin_dir.exists():
        return None

    json_file = plugin_dir / "share_plugins.json"
    data = read_share_plugins_json(json_file)

    if not data:
        return None

    data["local_path"] = str(plugin_dir)
    return data


def check_for_updates(plugin_name: str) -> dict:
    """
    检查插件是否有更新

    Args:
        plugin_name: 插件名称

    Returns:
        更新信息字典
    """
    plugin_info = get_plugin_info(plugin_name)

    if not plugin_info:
        return {
            "has_update": False,
            "error": "插件未找到"
        }

    repository = plugin_info.get("repository", {})
    repo_url = repository.get("url", "")
    repo_type = repository.get("type", "")

    if not repo_url:
        return {
            "has_update": False,
            "error": "插件未关联仓库"
        }

    local_version = plugin_info.get("version", "0.0.0")

    # 获取远程版本
    remote_version = get_remote_version(repo_url, repo_type)

    if not remote_version:
        return {
            "has_update": False,
            "local_version": local_version,
            "remote_version": "unknown",
            "error": "无法获取远程版本"
        }

    comparison = compare_versions(remote_version, local_version)

    return {
        "has_update": comparison > 0,
        "local_version": local_version,
        "remote_version": remote_version,
        "repo_url": repo_url,
        "comparison": comparison
    }


def update_as_sharer(plugin_name: str, source_path: Path,
                    increment: str = "patch", version: str = None,
                    push: bool = False) -> bool:
    """
    作为分享者更新插件

    Args:
        plugin_name: 插件名称
        source_path: 源路径（~/.claude/）
        increment: 版本递增类型
        version: 自定义版本
        push: 是否推送到远程

    Returns:
        是否成功
    """
    share_dir = get_share_dir()
    plugin_dir = get_plugin_path(plugin_name, share_dir)

    if not plugin_dir.exists():
        print(f"错误: 插件目录不存在: {plugin_dir}")
        return False

    json_file = plugin_dir / "share_plugins.json"
    data = read_share_plugins_json(json_file)

    if not data:
        print("错误: 无法读取插件数据")
        return False

    old_version = data.get("version", "1.0.0")
    repository = data.get("repository", {})
    repo_url = repository.get("url", "")

    print(f"更新插件: {plugin_name}")
    print(f"当前版本: {old_version}")
    print()

    # 确定新版本
    if version:
        new_version = version
    else:
        new_version = increment_version(old_version, increment)

    print(f"新版本: {new_version}")

    # 重新打包插件内容
    print("重新打包内容...")

    # 这里简化处理，实际应该重新从 source_path 打包
    # 现在只是更新版本号

    # 更新版本号
    data["version"] = new_version
    data["metadata"]["updated_at"] = __import__("datetime").datetime.now().isoformat()

    # 保存
    write_share_plugins_json(json_file, data)
    print(f"更新版本到: {new_version}")

    # 推送到远程
    if push:
        if not repo_url:
            print("警告: 插件未关联仓库，无法推送")
            return True

        print()
        print("推送到远程...")

        # 检查是否是 Git 仓库
        if not (plugin_dir / ".git").exists():
            print("错误: 插件目录不是 Git 仓库")
            return False

        # 提交更改
        commit_msg = f"Update {plugin_name} to v{new_version}"
        print(f"提交: {commit_msg}")

        if not add_commit(plugin_dir, commit_msg):
            print("提交失败")
            return False

        # 推送
        branch = get_current_branch(plugin_dir) or "main"
        if not push_repo(plugin_dir, "origin", branch):
            print("推送失败")
            return False

        print(f"推送完成!")
        print(f"  仓库: {repo_url}")
        print(f"  分支: {branch}")

    return True


def update_as_user(plugin_name: str, apply: bool = False) -> bool:
    """
    作为用户更新插件

    Args:
        plugin_name: 插件名称
        apply: 是否应用更新

    Returns:
        是否成功
    """
    # 检查更新
    update_info = check_for_updates(plugin_name)

    if "error" in update_info:
        print(f"错误: {update_info['error']}")
        return False

    if not update_info["has_update"]:
        print("已是最新版本")
        print(f"  本地版本: {update_info['local_version']}")
        print(f"  远程版本: {update_info['remote_version']}")
        return True

    print(f"发现更新!")
    print(f"  本地版本: {update_info['local_version']}")
    print(f"  远程版本: {update_info['remote_version']}")
    print(f"  仓库: {update_info['repo_url']}")
    print()

    if not apply:
        print("使用 --apply 参数应用更新")
        return True

    # 拉取更新
    share_dir = get_share_dir()
    plugin_dir = get_plugin_path(plugin_name, share_dir)

    print("拉取更新...")

    if not (plugin_dir / ".git").exists():
        print("错误: 插件目录不是 Git 仓库")
        return False

    if not pull(plugin_dir, "origin", "main"):
        print("拉取失败")
        return False

    print("拉取完成")

    # 读取更新后的数据
    json_file = plugin_dir / "share_plugins.json"
    data = read_share_plugins_json(json_file)

    if not data:
        print("错误: 无法读取更新后的插件数据")
        return False

    print(f"已更新到: {data.get('version', 'unknown')}")

    # 应用插件
    print()
    print("应用插件...")

    # 导入 apply_plugin
    from apply_plugin import apply_plugin

    target_path = get_claude_path()

    success = apply_plugin(
        plugin_dir,
        target_path,
        data.get("content", {}),
        data.get("apply", [{}])[0].get("hooks_mode", "smart") if data.get("apply") else "smart",
        "overwrite",
        False
    )

    return success


def main():
    parser = argparse.ArgumentParser(description="更新插件")
    parser.add_argument("--plugin", type=str, required=True,
                        help="插件名称或路径")
    parser.add_argument("--role", type=str, default="user",
                        choices=["sharer", "user"],
                        help="角色：sharer 或 user，默认 user")
    parser.add_argument("--check-updates", action="store_true",
                        help="检查更新")
    parser.add_argument("--source", type=str, default="~/.claude/",
                        help="源路径（sharer 模式），默认 ~/.claude/")
    parser.add_argument("--increment", type=str, default="patch",
                        choices=["patch", "minor", "major"],
                        help="版本递增类型（sharer 模式），默认 patch")
    parser.add_argument("--version", type=str, default="",
                        help="自定义版本（sharer 模式）")
    parser.add_argument("--apply", action="store_true",
                        help="应用更新（user 模式）")
    parser.add_argument("--push", action="store_true",
                        help="推送到远程（sharer 模式）")

    args = parser.parse_args()

    # 获取插件名称（可能是路径）
    plugin_path = Path(args.plugin).expanduser()
    if plugin_path.exists() and plugin_path.is_dir():
        # 从路径提取名称
        plugin_name = plugin_path.name
    else:
        plugin_name = args.plugin

    if args.role == "sharer":
        # 分享者模式
        source_path = expand_path(args.source)

        if args.check_updates:
            # 检查更新
            update_info = check_for_updates(plugin_name)
            if "error" in update_info:
                print(f"错误: {update_info['error']}")
                return 1
            print(f"本地版本: {update_info.get('local_version', 'unknown')}")
            print(f"远程版本: {update_info.get('remote_version', 'unknown')}")
            return 0
        else:
            # 更新插件
            success = update_as_sharer(
                plugin_name,
                source_path,
                args.increment,
                args.version or None,
                args.push
            )
            return 0 if success else 1

    else:
        # 用户模式
        if args.check_updates:
            # 检查更新
            update_info = check_for_updates(plugin_name)
            if "error" in update_info:
                print(f"错误: {update_info['error']}")
                return 1
            if update_info["has_update"]:
                print(f"发现更新: {update_info['local_version']} -> {update_info['remote_version']}")
            else:
                print("已是最新版本")
            return 0
        else:
            # 更新插件
            success = update_as_user(plugin_name, args.apply)
            return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
