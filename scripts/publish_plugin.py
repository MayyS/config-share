#!/usr/bin/env python3
"""
发布插件脚本
将插件发布到 GitHub、GitLab 或自定义仓库
"""
import argparse
import sys
import re
from pathlib import Path

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from git_utils import (
    check_repo_exists, create_repo, init_repo, add_commit,
    push_repo, create_tag, push_tags, add_remote, get_remotes,
    get_current_branch
)
from config_utils import read_share_plugins_json, validate_share_plugins_json


def validate_plugin_path(plugin_path: Path) -> bool:
    """
    验证插件路径是否有效

    Args:
        plugin_path: 插件路径

    Returns:
        是否有效
    """
    if not plugin_path.exists():
        print(f"错误: 插件目录不存在: {plugin_path}")
        return False

    if not plugin_path.is_dir():
        print(f"错误: 插件路径不是目录: {plugin_path}")
        return False

    json_file = plugin_path / "share_plugins.json"
    if not json_file.exists():
        print(f"错误: share_plugins.json 不存在: {json_file}")
        return False

    # 验证 JSON 格式
    data = read_share_plugins_json(json_file)
    if not data:
        print(f"错误: 无法读取 share_plugins.json")
        return False

    errors = validate_share_plugins_json(data)
    if errors:
        print("share_plugins.json 验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def parse_repo_url(url: str, repo_type: str) -> tuple:
    """
    解析仓库 URL

    Args:
        url: 仓库 URL
        repo_type: 仓库类型

    Returns:
        (repo_name, clean_url)
    """
    # 移除末尾的 .git
    clean_url = url.rstrip("/")
    if clean_url.endswith(".git"):
        clean_url = clean_url[:-4]

    # 提取仓库名
    if repo_type == "github":
        match = re.match(r".+/([^/]+)$", clean_url)
        if match:
            return match.group(1), clean_url
    elif repo_type == "gitlab":
        match = re.match(r".+/([^/]+)$", clean_url)
        if match:
            return match.group(1), clean_url
    else:
        # 自定义类型，尝试从 URL 提取
        match = re.match(r".+/([^/]+)$", clean_url)
        if match:
            return match.group(1), clean_url

    # 无法提取，使用默认名称
    return "plugin", clean_url


def publish_plugin(plugin_path: Path, repo_url: str, repo_type: str,
                    token: str = None, create_repo: bool = False,
                    commit_msg: str = None, tag: str = None,
                    push_only: bool = False) -> bool:
    """
    发布插件到仓库

    Args:
        plugin_path: 插件路径
        repo_url: 仓库 URL
        repo_type: 仓库类型
        token: 认证 Token
        create_repo: 是否创建新仓库
        commit_msg: 提交消息
        tag: 标签名称
        push_only: 仅推送（用于更新）

    Returns:
        是否成功
    """
    # 读取插件信息
    json_file = plugin_path / "share_plugins.json"
    data = read_share_plugins_json(json_file)
    plugin_name = data.get("plugin", "unknown")
    version = data.get("version", "1.0.0")

    print(f"发布插件: {plugin_name}")
    print(f"  版本: {version}")
    print(f"  仓库类型: {repo_type}")
    print(f"  仓库 URL: {repo_url}")
    print()

    # 解析仓库 URL
    repo_name, clean_url = parse_repo_url(repo_url, repo_type)
    print(f"仓库名: {repo_name}")
    print()

    # 检查仓库是否存在
    print("检查仓库...")
    repo_exists = check_repo_exists(repo_url, repo_type, token)

    if not repo_exists:
        if create_repo and repo_type != "custom":
            print(f"仓库不存在，尝试创建...")
            result = create_repo(repo_name, token, repo_type,
                               private=False,
                               description=data.get("description", ""))
            if result:
                print(f"  仓库创建成功: {result.get('html_url')}")
            else:
                print("  仓库创建失败")
                if repo_type == "gitlab":
                    print("  GitLab 仓库需要手动创建或提供项目 ID")
                return False
        elif repo_type == "custom":
            print("自定义仓库无法自动创建，请确保仓库已存在")
            return False
        else:
            print(f"仓库不存在，请使用 --create-repo 参数创建或手动创建")
            return False
    else:
        print("  仓库已存在")

    # 检查是否已是 Git 仓库
    is_git_repo = (plugin_path / ".git").exists()

    if push_only:
        # 仅推送模式
        print()
        print("仅推送模式...")

        if not is_git_repo:
            print("错误: 插件目录不是 Git 仓库")
            return False

        # 检查是否有 remote
        remotes = get_remotes(plugin_path)
        if "origin" not in remotes:
            # 添加 remote
            add_remote(plugin_path, "origin", repo_url)
            print("添加 remote: origin")

        # 提交更改
        commit_message = commit_msg or f"Update {plugin_name} to v{version}"
        print(f"提交: {commit_message}")
        if not add_commit(plugin_path, commit_message):
            print("提交失败")
            return False

        # 推送
        branch = get_current_branch(plugin_path) or "main"
        print(f"推送到 {branch} 分支...")
        if not push_repo(plugin_path, "origin", branch, token):
            print("推送失败")
            return False

    else:
        # 首次发布或完整发布
        print()
        print("准备发布...")

        if is_git_repo:
            print("插件目录已是 Git 仓库")
            remotes = get_remotes(plugin_path)
            if "origin" not in remotes:
                add_remote(plugin_path, "origin", repo_url)
                print("添加 remote: origin")
        else:
            # 初始化 Git 仓库
            print("初始化 Git 仓库...")
            if not init_repo(plugin_path):
                print("初始化失败")
                return False

            # 添加 remote
            add_remote(plugin_path, "origin", repo_url)
            print("添加 remote: origin")

        # 提交文件
        commit_message = commit_msg or f"Release {plugin_name} v{version}"
        print(f"提交: {commit_message}")
        if not add_commit(plugin_path, commit_message):
            print("提交失败")
            return False

        # 推送
        branch = get_current_branch(plugin_path) or "main"
        print(f"推送到 {branch} 分支...")
        if not push_repo(plugin_path, "origin", branch, token):
            print("推送失败")
            return False

        # 创建标签
        if not tag:
            tag = f"v{version}"

        print(f"创建标签: {tag}")
        if not create_tag(plugin_path, tag, f"Release {version}"):
            print("创建标签失败")
            # 继续推送，标签创建失败不影响发布

        # 推送标签
        print("推送标签...")
        if not push_tags(plugin_path, "origin", token):
            print("推送标签失败")
            # 继续执行

    print()
    print(f"发布完成! {repo_url}")
    return True


def main():
    parser = argparse.ArgumentParser(description="发布插件到仓库")
    parser.add_argument("--plugin", type=str, required=True,
                        help="插件路径")
    parser.add_argument("--repo", type=str, required=True,
                        help="仓库 URL（用户自定义）")
    parser.add_argument("--repo-type", type=str, default="github",
                        choices=["github", "gitlab", "custom"],
                        help="仓库类型，默认 github")
    parser.add_argument("--create-repo", action="store_true",
                        help="是否创建新仓库（不支持 custom 类型）")
    parser.add_argument("--token", type=str, default="",
                        help="认证 Token")
    parser.add_argument("--commit-msg", type=str, default="",
                        help="提交消息")
    parser.add_argument("--tag", type=str, default="",
                        help="标签名称，默认 v{version}")
    parser.add_argument("--push-only", action="store_true",
                        help="仅推送（用于更新）")

    args = parser.parse_args()

    # 解析插件路径
    plugin_path = Path(args.plugin).expanduser()

    # 验证插件
    if not validate_plugin_path(plugin_path):
        return 1

    # 获取 Token（支持环境变量）
    token = args.token
    if not token:
        if args.repo_type == "github":
            token = __import__("os").environ.get("GITHUB_TOKEN")
        elif args.repo_type == "gitlab":
            token = __import__("os").environ.get("GITLAB_TOKEN")

    # 发布插件
    success = publish_plugin(
        plugin_path,
        args.repo,
        args.repo_type,
        token,
        args.create_repo,
        args.commit_msg,
        args.tag,
        args.push_only
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
