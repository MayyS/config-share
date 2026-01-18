"""
Git 操作工具模块
支持 GitHub、GitLab 和自定义仓库的 Git 操作
"""
import os
import re
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
import json
import requests


# Git 配置
GIT_AUTHOR_NAME = "Config Share"
GIT_AUTHOR_EMAIL = "config-share@claude.ai"


def init_repo(path: Path) -> bool:
    """
    初始化 Git 仓库

    Args:
        path: 仓库路径

    Returns:
        是否成功
    """
    try:
        subprocess.run(
            ["git", "init"],
            cwd=path,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"初始化 Git 仓库失败: {e.stderr}")
        return False


def clone_repo(url: str, path: Path, token: Optional[str] = None, branch: str = "main") -> bool:
    """
    克隆仓库

    Args:
        url: 仓库 URL
        path: 目标路径
        token: 认证 Token
        branch: 分支名称

    Returns:
        是否成功
    """
    try:
        # 如果有 token，注入到 URL 中
        clone_url = url
        if token:
            clone_url = inject_token_to_url(url, token)

        args = ["git", "clone", "-b", branch, clone_url, str(path)]

        result = subprocess.run(
            args,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"克隆仓库失败: {e.stderr}")
        return False


def check_repo_exists(url: str, repo_type: str = "github", token: Optional[str] = None) -> bool:
    """
    检查仓库是否存在

    Args:
        url: 仓库 URL
        repo_type: 仓库类型 (github/gitlab/custom)
        token: 认证 Token

    Returns:
        是否存在
    """
    if repo_type == "custom":
        # 自定义仓库无法通过 API 检查，尝试 git ls-remote
        try:
            subprocess.run(
                ["git", "ls-remote", url],
                check=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return True
        except Exception:
            return False

    return check_repo_via_api(url, repo_type, token)


def check_repo_via_api(url: str, repo_type: str, token: Optional[str] = None) -> bool:
    """
    通过 API 检查仓库是否存在

    Args:
        url: 仓库 URL
        repo_type: 仓库类型
        token: 认证 Token

    Returns:
        是否存在
    """
    try:
        if repo_type == "github":
            return _check_github_repo(url, token)
        elif repo_type == "gitlab":
            return _check_gitlab_repo(url, token)
    except Exception as e:
        print(f"API 检查失败: {e}")
        return False

    return False


def _check_github_repo(url: str, token: Optional[str] = None) -> bool:
    """
    通过 GitHub API 检查仓库

    Args:
        url: 仓库 URL
        token: GitHub Token

    Returns:
        是否存在
    """
    # 解析 URL 获取 owner/repo
    match = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+)", url)
    if not match:
        return False

    owner, repo = match.groups()
    repo = repo.replace(".git", "")

    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    response = requests.get(api_url, headers=headers, timeout=10)
    return response.status_code == 200


def _check_gitlab_repo(url: str, token: Optional[str] = None) -> bool:
    """
    通过 GitLab API 检查仓库

    Args:
        url: 仓库 URL
        token: GitLab Token

    Returns:
        是否存在
    """
    # 解析 URL
    match = re.match(r"https?://(?:www\.)?gitlab\.com/(.+?)/?(?:\.git)?$", url)
    if not match:
        return False

    path = match.group(1)
    encoded_path = requests.utils.quote(path, safe="")

    api_url = f"https://gitlab.com/api/v4/projects/{encoded_path}"
    headers = {}
    if token:
        headers["PRIVATE-TOKEN"] = token

    response = requests.get(api_url, headers=headers, timeout=10)
    return response.status_code == 200


def create_repo(name: str, token: str, repo_type: str = "github",
                private: bool = False, description: str = "") -> Optional[Dict[str, Any]]:
    """
    创建新仓库

    Args:
        name: 仓库名称
        token: 认证 Token
        repo_type: 仓库类型 (github/gitlab)
        private: 是否私有
        description: 描述

    Returns:
        仓库信息，失败返回 None
    """
    try:
        if repo_type == "github":
            return _create_github_repo(name, token, private, description)
        elif repo_type == "gitlab":
            return _create_gitlab_repo(name, token, private, description)
    except Exception as e:
        print(f"创建仓库失败: {e}")
        return None

    return None


def _create_github_repo(name: str, token: str, private: bool, description: str) -> Optional[Dict[str, Any]]:
    """
    创建 GitHub 仓库

    Args:
        name: 仓库名称
        token: GitHub Token
        private: 是否私有
        description: 描述

    Returns:
        仓库信息
    """
    api_url = "https://api.github.com/user/repos"
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    data = {
        "name": name,
        "private": private,
        "description": description,
        "auto_init": False
    }

    response = requests.post(api_url, json=data, headers=headers, timeout=30)

    if response.status_code == 201:
        return response.json()
    else:
        print(f"GitHub API 错误: {response.status_code} - {response.text}")
        return None


def _create_gitlab_repo(name: str, token: str, private: bool, description: str) -> Optional[Dict[str, Any]]:
    """
    创建 GitLab 仓库

    Args:
        name: 仓库名称
        token: GitLab Token
        private: 是否私有
        description: 描述

    Returns:
        仓库信息
    """
    # GitLab 创建仓库需要 project_id（用户ID或组ID）
    # 这里简化处理，返回 None，提示用户手动创建
    print(f"GitLab 仓库创建需要指定项目路径，请手动创建或提供项目 ID")
    return None


def add_commit(repo_path: Path, message: str, files: Optional[List[str]] = None) -> bool:
    """
    添加文件并提交

    Args:
        repo_path: 仓库路径
        message: 提交消息
        files: 要添加的文件列表（None 表示添加所有）

    Returns:
        是否成功
    """
    try:
        # 配置 Git
        subprocess.run(
            ["git", "config", "user.name", GIT_AUTHOR_NAME],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        subprocess.run(
            ["git", "config", "user.email", GIT_AUTHOR_EMAIL],
            cwd=repo_path,
            check=True,
            capture_output=True
        )

        # 添加文件
        if files:
            for f in files:
                subprocess.run(
                    ["git", "add", f],
                    cwd=repo_path,
                    check=True,
                    capture_output=True
                )
        else:
            subprocess.run(
                ["git", "add", "."],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

        # 提交
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=repo_path,
            check=True,
            capture_output=True
        )

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git 提交失败: {e.stderr}")
        return False


def push_repo(repo_path: Path, remote: str = "origin",
             branch: str = "main", token: Optional[str] = None) -> bool:
    """
    推送到远程仓库

    Args:
        repo_path: 仓库路径
        remote: 远程名称
        branch: 分支名称
        token: 认证 Token

    Returns:
        是否成功
    """
    try:
        # 如果有 token，配置 Git 凭证
        if token:
            # 获取 remote URL
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            url = result.stdout.strip()
            url_with_token = inject_token_to_url(url, token)

            # 设置带 token 的 URL
            subprocess.run(
                ["git", "remote", "set-url", remote, url_with_token],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

        # 推送
        subprocess.run(
            ["git", "push", "-u", remote, branch],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=60
        )

        # 恢复不带 token 的 URL
        if token:
            subprocess.run(
                ["git", "remote", "set-url", remote, url],
                cwd=repo_path,
                capture_output=True  # 忽略错误
            )

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git 推送失败: {e.stderr}")
        return False


def create_tag(repo_path: Path, tag_name: str, message: str = "") -> bool:
    """
    创建 Git 标签

    Args:
        repo_path: 仓库路径
        tag_name: 标签名称
        message: 标签消息

    Returns:
        是否成功
    """
    try:
        args = ["git", "tag", "-a", tag_name]
        if message:
            args.extend(["-m", message])
        else:
            args.extend(["-m", f"Release {tag_name}"])

        subprocess.run(
            args,
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"创建标签失败: {e.stderr}")
        return False


def push_tags(repo_path: Path, remote: str = "origin", token: Optional[str] = None) -> bool:
    """
    推送标签到远程

    Args:
        repo_path: 仓库路径
        remote: 远程名称
        token: 认证 Token

    Returns:
        是否成功
    """
    try:
        # 配置凭证（如果需要）
        if token:
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            url = result.stdout.strip()
            url_with_token = inject_token_to_url(url, token)
            subprocess.run(
                ["git", "remote", "set-url", remote, url_with_token],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

        subprocess.run(
            ["git", "push", "--tags"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=60
        )

        # 恢复 URL
        if token:
            subprocess.run(
                ["git", "remote", "set-url", remote, url],
                cwd=repo_path,
                capture_output=True
            )

        return True
    except subprocess.CalledProcessError as e:
        print(f"推送标签失败: {e.stderr}")
        return False


def get_remote_version(url: str, repo_type: str = "github",
                       token: Optional[str] = None) -> Optional[str]:
    """
    获取远程仓库的最新版本（通过 Git 标签）

    Args:
        url: 仓库 URL
        repo_type: 仓库类型
        token: 认证 Token

    Returns:
        最新版本标签，失败返回 None
    """
    try:
        # 克隆到临时目录
        temp_dir = Path.home() / ".cache" / "config-share" / "temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        temp_repo = temp_dir / "check_version"

        # 删除旧的临时目录
        if temp_repo.exists():
            import shutil
            shutil.rmtree(temp_repo)

        if not clone_repo(url, temp_repo, token):
            return None

        # 获取所有标签
        result = subprocess.run(
            ["git", "tag", "-l", "v*"],
            cwd=temp_repo,
            check=True,
            capture_output=True,
            text=True
        )

        tags = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # 清理临时目录
        import shutil
        shutil.rmtree(temp_repo)

        if not tags:
            return None

        # 过滤掉 'v' 前缀并排序
        versions = [tag.lstrip("v") for tag in tags if tag]
        versions.sort(key=lambda v: [int(x) for x in v.replace("-", ".").split(".")[0:3]], reverse=True)

        if versions:
            return versions[0]

        return None
    except Exception as e:
        print(f"获取远程版本失败: {e}")
        return None


def inject_token_to_url(url: str, token: str) -> str:
    """
    将 Token 注入到 Git URL 中

    Args:
        url: 原始 URL
        token: Token

    Returns:
        带 Token 的 URL
    """
    if not token:
        return url

    # HTTPS URL
    if url.startswith("https://"):
        return re.sub(
            r"https://",
            f"https://oauth2:{token}@",
            url
        )

    # 其他格式，尝试注入
    if "://" in url:
        protocol, rest = url.split("://", 1)
        if "@" in rest:
            # 已有认证，替换
            return f"{protocol}://oauth2:{token}@{rest.split('@', 1)[1]}"
        else:
            return f"{protocol}://oauth2:{token}@{rest}"

    return url


def get_current_branch(repo_path: Path) -> Optional[str]:
    """
    获取当前分支

    Args:
        repo_path: 仓库路径

    Returns:
        分支名称，失败返回 None
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None


def fetch(repo_path: Path, remote: str = "origin", token: Optional[str] = None) -> bool:
    """
    从远程获取更新

    Args:
        repo_path: 仓库路径
        remote: 远程名称
        token: 认证 Token

    Returns:
        是否成功
    """
    try:
        # 配置凭证
        if token:
            result = subprocess.run(
                ["git", "remote", "get-url", remote],
                cwd=repo_path,
                check=True,
                capture_output=True,
                text=True
            )
            url = result.stdout.strip()
            url_with_token = inject_token_to_url(url, token)
            subprocess.run(
                ["git", "remote", "set-url", remote, url_with_token],
                cwd=repo_path,
                check=True,
                capture_output=True
            )

        subprocess.run(
            ["git", "fetch", remote],
            cwd=repo_path,
            check=True,
            capture_output=True,
            timeout=60
        )

        # 恢复 URL
        if token:
            subprocess.run(
                ["git", "remote", "set-url", remote, url],
                cwd=repo_path,
                capture_output=True
            )

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git fetch 失败: {e.stderr}")
        return False


def pull(repo_path: Path, remote: str = "origin", branch: str = "main",
         token: Optional[str] = None) -> bool:
    """
    拉取并合并远程更新

    Args:
        repo_path: 仓库路径
        remote: 远程名称
        branch: 分支名称
        token: 认证 Token

    Returns:
        是否成功
    """
    try:
        # Fetch
        if not fetch(repo_path, remote, token):
            return False

        # Merge
        subprocess.run(
            ["git", "merge", f"{remote}/{branch}"],
            cwd=repo_path,
            check=True,
            capture_output=True
        )

        return True
    except subprocess.CalledProcessError as e:
        print(f"Git pull 失败: {e.stderr}")
        return False


def add_remote(repo_path: Path, name: str, url: str) -> bool:
    """
    添加远程仓库

    Args:
        repo_path: 仓库路径
        name: 远程名称
        url: 远程 URL

    Returns:
        是否成功
    """
    try:
        subprocess.run(
            ["git", "remote", "add", name, url],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"添加远程仓库失败: {e.stderr}")
        return False


def get_remotes(repo_path: Path) -> Dict[str, str]:
    """
    获取所有远程仓库

    Args:
        repo_path: 仓库路径

    Returns:
        远程名称到 URL 的映射
    """
    try:
        result = subprocess.run(
            ["git", "remote", "-v"],
            cwd=repo_path,
            check=True,
            capture_output=True,
            text=True
        )

        remotes = {}
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split()
            if len(parts) >= 2:
                name, url = parts[0], parts[1]
                remotes[name] = url

        return remotes
    except subprocess.CalledProcessError:
        return {}
