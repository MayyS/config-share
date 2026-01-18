"""
文件操作工具模块
提供文件复制、冲突检测、配置读取等功能
"""
import os
import json
import shutil
import copy
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import re


def copy_with_conflict(src: Path, dst: Path, mode: str = "ask") -> Tuple[bool, str]:
    """
    复制文件，处理可能的冲突

    Args:
        src: 源文件路径
        dst: 目标文件路径
        mode: 冲突处理模式 (ask/overwrite/skip/rename)

    Returns:
        (success, message): 操作是否成功及消息
    """
    if not src.exists():
        return False, f"源文件不存在: {src}"

    # 确保目标目录存在
    dst.parent.mkdir(parents=True, exist_ok=True)

    # 检查目标文件是否存在
    if dst.exists():
        if mode == "skip":
            return True, f"跳过已存在文件: {dst}"

        if mode == "rename":
            # 找到可用的重命名
            counter = 1
            while True:
                new_name = f"{dst.stem}_{counter}{dst.suffix}"
                new_dst = dst.parent / new_name
                if not new_dst.exists():
                    dst = new_dst
                    break
                counter += 1

        elif mode == "ask":
            # 在实际使用中应由调用者处理交互
            return False, f"文件冲突: {dst} (需要用户选择)"

    try:
        shutil.copy2(src, dst)
        return True, f"成功复制: {src} -> {dst}"
    except Exception as e:
        return False, f"复制失败: {e}"


def detect_conflicts(src_files: List[Path], dst_dir: Path) -> List[Dict[str, str]]:
    """
    检测源文件与目标目录的冲突

    Args:
        src_files: 源文件列表
        dst_dir: 目标目录

    Returns:
        冲突文件列表，每项包含 src 和 dst
    """
    conflicts = []
    for src_file in src_files:
        rel_path = src_file.relative_to(src_file.parent.parent.parent)
        dst_file = dst_dir / rel_path
        if dst_file.exists():
            conflicts.append({
                "src": str(src_file),
                "dst": str(dst_file),
                "relative": str(rel_path)
            })
    return conflicts


def safe_delete(path: Path) -> bool:
    """
    安全删除文件或目录

    Args:
        path: 要删除的路径

    Returns:
        是否删除成功
    """
    try:
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        print(f"删除失败 {path}: {e}")
        return False


def ensure_dirs_exist(paths: List[Path]) -> None:
    """
    确保目录存在

    Args:
        paths: 目录路径列表
    """
    for path in paths:
        path.mkdir(parents=True, exist_ok=True)


def read_agents(agent_dir: Path) -> Dict[str, Dict[str, Any]]:
    """
    读取所有 agent 文件

    Args:
        agent_dir: agent 目录路径

    Returns:
        agent 名称到内容的字典
    """
    agents = {}
    if not agent_dir.exists():
        return agents

    for agent_file in agent_dir.glob("*.md"):
        try:
            content = agent_file.read_text(encoding="utf-8")
            # 解析 frontmatter
            frontmatter = parse_frontmatter(content)
            if frontmatter:
                agents[agent_file.stem] = {
                    "file": str(agent_file),
                    "frontmatter": frontmatter,
                    "content": content
                }
        except Exception as e:
            print(f"读取 agent 失败 {agent_file}: {e}")

    return agents


def read_commands(command_dir: Path) -> Dict[str, str]:
    """
    读取所有 command 文件

    Args:
        command_dir: command 目录路径

    Returns:
        command 名称到文件路径的字典
    """
    commands = {}
    if not command_dir.exists():
        return commands

    for cmd_file in command_dir.glob("*.md"):
        try:
            content = cmd_file.read_text(encoding="utf-8")
            commands[cmd_file.stem] = {
                "file": str(cmd_file),
                "content": content
            }
        except Exception as e:
            print(f"读取 command 失败 {cmd_file}: {e}")

    return commands


def parse_frontmatter(content: str) -> Optional[Dict[str, Any]]:
    """
    解析 YAML frontmatter

    Args:
        content: 文件内容

    Returns:
        解析出的 frontmatter 字典，如果没有则返回 None
    """
    # 匹配 --- 包围的 YAML
    pattern = r"^---\n(.*?)\n---"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return None

    try:
        import yaml
        return yaml.safe_load(match.group(1))
    except ImportError:
        # 如果没有 yaml 模块，返回 None
        return None
    except Exception:
        return None


def merge_hooks(existing_hooks: Dict[str, List[Dict[str, Any]]],
                new_hooks: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    智能合并 hooks（Smart 模式）

    策略:
    - 对于已存在的 hook 事件，保留用户自定义的 hooks
    - 只添加插件中新增的 hook 配置
    - 如果同一事件下有完全相同的命令，跳过

    Args:
        existing_hooks: 现有的 hooks.json 内容
        new_hooks: 新的 hooks 内容

    Returns:
        合并后的 hooks
    """
    merged = copy.deepcopy(existing_hooks)

    for event_name, event_hooks in new_hooks.items():
        if event_name not in merged:
            # 新事件，直接添加
            merged[event_name] = copy.deepcopy(event_hooks)
        else:
            # 现有事件，合并 hooks
            for new_hook in event_hooks:
                if not is_duplicate_hook(new_hook, merged[event_name]):
                    merged[event_name].append(copy.deepcopy(new_hook))

    return merged


def is_duplicate_hook(hook: Dict[str, Any],
                       existing_hooks: List[Dict[str, Any]]) -> bool:
    """
    检查 hook 是否重复

    Args:
        hook: 要检查的 hook
        existing_hooks: 现有的 hooks 列表

    Returns:
        是否重复
    """
    for existing in existing_hooks:
        if hooks_equal(hook, existing):
            return True
    return False


def hooks_equal(hook1: Dict[str, Any], hook2: Dict[str, Any]) -> bool:
    """
    比较两个 hook 是否相等

    Args:
        hook1: 第一个 hook
        hook2: 第二个 hook

    Returns:
        是否相等
    """
    # 比较关键字段
    if hook1.get("type") != hook2.get("type"):
        return False

    if hook1.get("type") == "tool_use":
        # 对于 tool_use 类型，比较 tool 名称
        if hook1.get("tool_name") != hook2.get("tool_name"):
            return False
        if hook1.get("when") != hook2.get("when"):
            return False
    elif hook1.get("type") == "user_prompt_submit":
        # 对于 user_prompt_submit 类型，比较 pattern
        if hook1.get("pattern") != hook2.get("pattern"):
            return False

    return True


def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    安全加载 JSON 文件

    Args:
        file_path: JSON 文件路径

    Returns:
        JSON 内容，失败返回 None
    """
    if not file_path.exists():
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"加载 JSON 失败 {file_path}: {e}")
        return None


def save_json(file_path: Path, data: Dict[str, Any], indent: int = 2) -> bool:
    """
    保存 JSON 文件

    Args:
        file_path: JSON 文件路径
        data: 要保存的数据
        indent: 缩进空格数

    Returns:
        是否成功
    """
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"保存 JSON 失败 {file_path}: {e}")
        return False


def get_claude_path() -> Path:
    """
    获取 Claude 配置目录路径

    Returns:
        Claude 配置目录路径
    """
    return Path.home() / ".claude"


def get_share_dir() -> Path:
    """
    获取插件共享目录路径（当前项目目录）

    Returns:
        插件共享目录路径
    """
    return Path.cwd() / "claude_share"


def expand_path(path: str) -> Path:
    """
    展开路径（处理 ~ 和环境变量）

    Args:
        path: 路径字符串

    Returns:
        展开后的 Path 对象
    """
    return Path(os.path.expandvars(os.path.expanduser(path)))


def list_directory(path: Path, pattern: str = "*") -> List[Path]:
    """
    列出目录下的文件

    Args:
        path: 目录路径
        pattern: 匹配模式

    Returns:
        文件路径列表
    """
    if not path.exists():
        return []
    return list(path.glob(pattern))


def is_subdirectory(child: Path, parent: Path) -> bool:
    """
    检查 child 是否是 parent 的子目录

    Args:
        child: 子目录路径
        parent: 父目录路径

    Returns:
        是否是子目录
    """
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False
