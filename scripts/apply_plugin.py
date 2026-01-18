#!/usr/bin/env python3
"""
应用插件脚本
从远程仓库或本地路径下载并应用插件
"""
import argparse
import sys
import tempfile
import shutil
from pathlib import Path

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from git_utils import clone_repo, pull
from file_utils import (
    expand_path, copy_with_conflict, detect_conflicts,
    load_json, save_json, merge_hooks, get_claude_path, get_share_dir,
    ensure_dirs_exist
)
from config_utils import (
    read_share_plugins_json, validate_share_plugins_json,
    get_plugin_path, update_apply_record
)
from sanitize_utils import (
    find_env_files, count_placeholders, parse_env_example
)


def is_url(source: str) -> bool:
    """
    检查是否为 URL

    Args:
        source: 源字符串

    Returns:
        是否为 URL
    """
    return source.startswith("http://") or source.startswith("https://")


def download_plugin(source: str, download_dir: Path) -> Path:
    """
    下载/克隆插件

    Args:
        source: 插件来源（URL 或路径）
        download_dir: 下载目录

    Returns:
        插件目录路径
    """
    if is_url(source):
        # 克隆仓库
        print(f"从 {source} 克隆插件...")
        repo_name = source.rstrip("/").split("/")[-1].replace(".git", "")
        plugin_path = download_dir / repo_name

        # 删除旧目录
        if plugin_path.exists():
            shutil.rmtree(plugin_path)

        if not clone_repo(source, plugin_path):
            print("克隆失败")
            return None

        return plugin_path
    else:
        # 本地路径
        local_path = Path(source).expanduser()
        if not local_path.exists():
            print(f"本地路径不存在: {local_path}")
            return None

        # 复制到下载目录
        plugin_name = local_path.name
        plugin_path = download_dir / plugin_name

        if plugin_path.exists():
            shutil.rmtree(plugin_path)

        shutil.copytree(local_path, plugin_path)
        return plugin_path


def validate_plugin(plugin_path: Path) -> bool:
    """
    验证插件

    Args:
        plugin_path: 插件路径

    Returns:
        是否有效
    """
    json_file = plugin_path / "share_plugins.json"
    if not json_file.exists():
        print(f"错误: share_plugins.json 不存在")
        return False

    data = read_share_plugins_json(json_file)
    if not data:
        print(f"错误: 无法读取 share_plugins.json")
        return False

    errors = validate_share_plugins_json(data)
    if errors:
        print("插件验证失败:")
        for error in errors:
            print(f"  - {error}")
        return False

    return True


def check_conflicts(plugin_path: Path, target_path: Path,
                   content_filter: dict = None) -> list:
    """
    检查文件冲突

    Args:
        plugin_path: 插件路径
        target_path: 目标路径
        content_filter: 内容过滤器

    Returns:
        冲突文件列表
    """
    conflicts = []

    data = read_share_plugins_json(plugin_path / "share_plugins.json")
    if not data:
        return conflicts

    content = data.get("content", {})

    # 检查 commands
    commands_list = content.get("commands", [])
    if commands_list and (not content_filter or content_filter.get("commands")):
        commands_dir = plugin_path / "commands"
        target_commands_dir = target_path / "commands"

        if commands_list == ["all"]:
            for cmd_file in commands_dir.glob("*.md"):
                dst = target_commands_dir / cmd_file.name
                if dst.exists():
                    conflicts.append({
                        "type": "command",
                        "file": cmd_file.name,
                        "path": str(dst)
                    })
        else:
            for cmd_name in commands_list:
                src = commands_dir / f"{cmd_name}.md"
                dst = target_commands_dir / f"{cmd_name}.md"
                if src.exists() and dst.exists():
                    conflicts.append({
                        "type": "command",
                        "file": cmd_name,
                        "path": str(dst)
                    })

    # 检查 agents
    agents_list = content.get("agents", [])
    if agents_list and (not content_filter or content_filter.get("agents")):
        agents_dir = plugin_path / "agents"
        target_agents_dir = target_path / "agents"

        for agent_name in agents_list:
            src = agents_dir / f"{agent_name}.md"
            dst = target_agents_dir / f"{agent_name}.md"
            if src.exists() and dst.exists():
                conflicts.append({
                    "type": "agent",
                    "file": agent_name,
                    "path": str(dst)
                })

    # 检查 hooks
    hooks_list = content.get("hooks", [])
    if hooks_list and (not content_filter or content_filter.get("hooks")):
        hooks_file = plugin_path / "hooks.json"
        target_hooks_file = target_path / "hooks.json"
        if hooks_file.exists() and target_hooks_file.exists():
            conflicts.append({
                "type": "hooks",
                "file": "hooks.json",
                "path": str(target_hooks_file)
            })

    # 检查 mcp
    mcp_list = content.get("mcp", [])
    if mcp_list and (not content_filter or content_filter.get("mcp")):
        mcp_file = plugin_path / "mcp.json"
        target_mcp_file = target_path / "mcp.json"
        if mcp_file.exists() and target_mcp_file.exists():
            conflicts.append({
                "type": "mcp",
                "file": "mcp.json",
                "path": str(target_mcp_file)
            })

    # 检查 skills
    skills_list = content.get("skills", [])
    if skills_list and (not content_filter or content_filter.get("skills")):
        skills_dir = plugin_path / "skills"
        target_skills_dir = target_path / "skills"

        if skills_list == ["all"]:
            for skill_dir in skills_dir.glob("*"):
                if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                    dst = target_skills_dir / skill_dir.name
                    if dst.exists():
                        conflicts.append({
                            "type": "skill",
                            "file": skill_dir.name,
                            "path": str(dst)
                        })
        else:
            for skill_name in skills_list:
                src = skills_dir / skill_name
                dst = target_skills_dir / skill_name
                if src.exists() and dst.exists():
                    conflicts.append({
                        "type": "skill",
                        "file": skill_name,
                        "path": str(dst)
                    })

    return conflicts


def apply_plugin(plugin_path: Path, target_path: Path,
                content_filter: dict = None,
                hooks_mode: str = "smart",
                conflict_mode: str = "ask",
                dry_run: bool = False) -> bool:
    """
    应用插件到目标路径

    Args:
        plugin_path: 插件路径
        target_path: 目标路径
        content_filter: 内容过滤器
        hooks_mode: hooks 处理模式
        conflict_mode: 冲突处理模式
        dry_run: 试运行

    Returns:
        是否成功
    """
    data = read_share_plugins_json(plugin_path / "share_plugins.json")
    if not data:
        print("错误: 无法读取插件数据")
        return False

    content = data.get("content", {})
    plugin_name = data.get("plugin", "unknown")
    version = data.get("version", "1.0.0")

    print(f"应用插件: {plugin_name} v{version}")
    print(f"目标路径: {target_path}")
    print(f"Hooks 模式: {hooks_mode}")
    print(f"冲突处理: {conflict_mode}")
    print()

    # 确保目标目录存在
    ensure_dirs_exist([target_path])

    # 构建实际应用的内容
    apply_content = {}
    if content_filter:
        apply_content = content_filter
    else:
        apply_content = content

    file_count = 0

    # 应用 commands
    if apply_content.get("commands"):
        print("应用 Commands:")
        commands_list = apply_content["commands"]
        commands_dir = plugin_path / "commands"
        target_commands_dir = target_path / "commands"

        if not dry_run:
            ensure_dirs_exist([target_commands_dir])

        if commands_list == ["all"]:
            for cmd_file in commands_dir.glob("*.md"):
                dst = target_commands_dir / cmd_file.name

                if dry_run:
                    print(f"  [DRY RUN] 会复制: {cmd_file.name}")
                else:
                    success, msg = copy_with_conflict(cmd_file, dst, conflict_mode)
                    if success:
                        file_count += 1
                        if not dry_run:
                            print(f"    {msg}")
                    else:
                        print(f"    {msg}")
        else:
            for cmd_name in commands_list:
                src = commands_dir / f"{cmd_name}.md"
                dst = target_commands_dir / f"{cmd_name}.md"

                if not src.exists():
                    print(f"    跳过（不存在）: {cmd_name}")
                    continue

                if dry_run:
                    print(f"  [DRY RUN] 会复制: {cmd_name}")
                else:
                    success, msg = copy_with_conflict(src, dst, conflict_mode)
                    if success:
                        file_count += 1
                        print(f"    {msg}")
                    else:
                        print(f"    {msg}")

    # 应用 agents
    if apply_content.get("agents"):
        print("应用 Agents:")
        agents_list = apply_content["agents"]
        agents_dir = plugin_path / "agents"
        target_agents_dir = target_path / "agents"

        if not dry_run:
            ensure_dirs_exist([target_agents_dir])

        for agent_name in agents_list:
            src = agents_dir / f"{agent_name}.md"
            dst = target_agents_dir / f"{agent_name}.md"

            if not src.exists():
                print(f"    跳过（不存在）: {agent_name}")
                continue

            if dry_run:
                print(f"  [DRY RUN] 会复制: {agent_name}")
            else:
                success, msg = copy_with_conflict(src, dst, conflict_mode)
                if success:
                    file_count += 1
                    print(f"    {msg}")
                else:
                    print(f"    {msg}")

    # 应用 hooks
    if apply_content.get("hooks"):
        print("应用 Hooks:")
        hooks_file = plugin_path / "hooks.json"
        target_hooks_file = target_path / "hooks.json"

        if not hooks_file.exists():
            print(f"    跳过（不存在）: hooks.json")
        elif dry_run:
            print(f"  [DRY RUN] 会处理 hooks.json (模式: {hooks_mode})")
        else:
            if hooks_mode == "skip":
                print(f"    跳过 (skip 模式)")
            elif hooks_mode == "replace":
                success, msg = copy_with_conflict(hooks_file, target_hooks_file, "overwrite")
                if success:
                    file_count += 1
                    print(f"    {msg}")
                else:
                    print(f"    {msg}")
            else:  # smart
                # 智能合并
                existing_hooks = load_json(target_hooks_file) or {}
                new_hooks = load_json(hooks_file) or {}

                merged = merge_hooks(existing_hooks, new_hooks)
                save_json(target_hooks_file, merged)
                file_count += 1
                print(f"    智能合并完成: {target_hooks_file}")

    # 应用 mcp
    if apply_content.get("mcp"):
        print("应用 MCP:")
        mcp_file = plugin_path / "mcp.json"
        target_mcp_file = target_path / "mcp.json"

        if not mcp_file.exists():
            print(f"    跳过（不存在）: mcp.json")
        elif dry_run:
            print(f"  [DRY RUN] 会复制: mcp.json")
        else:
            success, msg = copy_with_conflict(mcp_file, target_mcp_file, conflict_mode)
            if success:
                file_count += 1
                print(f"    {msg}")
            else:
                print(f"    {msg}")

    # 应用 skills
    if apply_content.get("skills"):
        print("应用 Skills:")
        skills_list = apply_content["skills"]
        skills_dir = plugin_path / "skills"
        target_skills_dir = target_path / "skills"

        if not dry_run:
            ensure_dirs_exist([target_skills_dir])

        if skills_list == ["all"]:
            for skill_dir in skills_dir.glob("*"):
                if skill_dir.is_dir() and not skill_dir.name.startswith('.'):
                    dst = target_skills_dir / skill_dir.name

                    if dry_run:
                        print(f"  [DRY RUN] 会复制目录: {skill_dir.name}")
                    else:
                        try:
                            if dst.exists():
                                if conflict_mode == "ask":
                                    response = input(f"    {skill_dir.name} 已存在，是否覆盖？(y/N): ")
                                    if response.lower() != 'y':
                                        print(f"    跳过: {skill_dir.name}")
                                        continue
                                elif conflict_mode == "skip":
                                    print(f"    跳过（已存在）: {skill_dir.name}")
                                    continue
                                shutil.rmtree(dst)

                            shutil.copytree(skill_dir, dst)
                            file_count += 1
                            print(f"    成功复制: {skill_dir.name}")
                        except Exception as e:
                            print(f"    复制失败: {skill_dir.name} - {e}")
        else:
            for skill_name in skills_list:
                src = skills_dir / skill_name
                dst = target_skills_dir / skill_name

                if not src.exists():
                    print(f"    跳过（不存在）: {skill_name}")
                    continue

                if dry_run:
                    print(f"  [DRY RUN] 会复制目录: {skill_name}")
                else:
                    try:
                        if dst.exists():
                            if conflict_mode == "ask":
                                response = input(f"    {skill_name} 已存在，是否覆盖？(y/N): ")
                                if response.lower() != 'y':
                                    print(f"    跳过: {skill_name}")
                                    continue
                            elif conflict_mode == "skip":
                                print(f"    跳过（已存在）: {skill_name}")
                                continue
                            shutil.rmtree(dst)

                        shutil.copytree(src, dst)
                        file_count += 1
                        print(f"    成功复制: {skill_name}")
                    except Exception as e:
                        print(f"    复制失败: {skill_name} - {e}")

    # 更新应用记录
    print()
    if not dry_run:
        update_apply_record(data, str(target_path), apply_content, {}, hooks_mode)

        # 复制插件到本地缓存
        share_dir = get_share_dir()
        ensure_dirs_exist([share_dir])
        local_plugin_dir = share_dir / plugin_name

        if local_plugin_dir.exists():
            shutil.rmtree(local_plugin_dir)

        shutil.copytree(plugin_path, local_plugin_dir)

        # 保存更新后的 share_plugins.json
        json_file = local_plugin_dir / "share_plugins.json"
        save_json(json_file, data)

        print(f"插件已缓存到: {local_plugin_dir}")
        print(f"更新应用记录到: share_plugins.json")

    # 检查环境变量配置
    env_files = find_env_files(plugin_path)
    if env_files and not dry_run:
        print()
        print("=" * 60)
        print("环境变量配置提示")
        print("=" * 60)

        env_example = plugin_path / ".env.example"
        if env_example.exists():
            env_vars = parse_env_example(env_example)
            print(f"检测到 {len(env_vars)} 个环境变量需要配置:")
            for key in env_vars.keys():
                print(f"  - {key}")

            print()
            print("配置步骤:")
            print(f"  1. 复制示例文件: cp {env_example} .env")
            print(f"  2. 编辑 .env 文件，填入真实的环境变量值")
            print(f"  3. 确保环境变量在运行时可访问（通过 export 或 dotenv）")

            # 检查 hooks.json 和 mcp.json 中的占位符
            placeholder_count = 0
            if (target_path / "hooks.json").exists():
                hooks_data = load_json(target_path / "hooks.json")
                placeholder_count += count_placeholders(hooks_data)
            if (target_path / "mcp.json").exists():
                mcp_data = load_json(target_path / "mcp.json")
                placeholder_count += count_placeholders(mcp_data)

            if placeholder_count > 0:
                print(f"  4. 配置文件中包含 {placeholder_count} 个环境变量占位符 (${{VAR_NAME}})")

        print("=" * 60)

    print()
    print(f"完成! 应用了 {file_count} 个文件")

    return True


def main():
    parser = argparse.ArgumentParser(description="应用插件到本地")
    parser.add_argument("--source", type=str, required=True,
                        help="插件来源（URL 或本地路径）")
    parser.add_argument("--target", type=str, default="~/.claude/",
                        help="目标路径，默认 ~/.claude/")
    parser.add_argument("--download", action="store_true",
                        help="仅下载，不应用")
    parser.add_argument("--check-conflicts", action="store_true",
                        help="仅检查冲突")
    parser.add_argument("--apply", action="store_true",
                        help="应用插件")
    parser.add_argument("--commands", type=str, default="",
                        help="要应用的 commands (all 或逗号分隔)")
    parser.add_argument("--agents", type=str, default="",
                        help="要应用的 agents (逗号分隔)")
    parser.add_argument("--hooks", type=str, default="smart",
                        choices=["smart", "replace", "skip"],
                        help="hooks 处理模式")
    parser.add_argument("--mcp", action="store_true",
                        help="是否应用 mcp")
    parser.add_argument("--skills", type=str, default="",
                        help="要应用的 skills (all 或逗号分隔)")
    parser.add_argument("--conflict-mode", type=str, default="ask",
                        choices=["ask", "overwrite", "skip", "rename"],
                        help="冲突处理模式")
    parser.add_argument("--dry-run", action="store_true",
                        help="试运行")

    args = parser.parse_args()

    # 解析路径
    target_path = expand_path(args.target)

    # 下载插件到临时目录
    temp_dir = Path(tempfile.gettempdir()) / "config-share" / "download"
    temp_dir.mkdir(parents=True, exist_ok=True)

    print(f"下载插件...")
    plugin_path = download_plugin(args.source, temp_dir)

    if not plugin_path:
        print("下载失败")
        return 1

    print(f"插件已下载到: {plugin_path}")
    print()

    # 验证插件
    if not validate_plugin(plugin_path):
        return 1

    # 如果仅下载，退出
    if args.download:
        print("下载完成")
        return 0

    # 检查冲突
    if args.check_conflicts:
        print("检查冲突...")
        conflicts = check_conflicts(plugin_path, target_path)

        if conflicts:
            print(f"\n发现 {len(conflicts)} 个冲突:")
            for conflict in conflicts:
                print(f"  [{conflict['type'].upper()}] {conflict['file']}")
        else:
            print("未发现冲突")

        return 0

    # 应用插件
    if args.apply:
        # 构建内容过滤器
        content_filter = {}

        if args.commands:
            if args.commands == "all":
                content_filter["commands"] = ["all"]
            else:
                content_filter["commands"] = [c.strip() for c in args.commands.split(",") if c.strip()]

        if args.agents:
            content_filter["agents"] = [a.strip() for a in args.agents.split(",") if a.strip()]

        if args.hooks != "smart" or args.mcp:
            content_filter["hooks"] = ["hooks.json"]

        if args.mcp:
            content_filter["mcp"] = ["mcp.json"]

        if args.skills:
            if args.skills == "all":
                content_filter["skills"] = ["all"]
            else:
                content_filter["skills"] = [s.strip() for s in args.skills.split(",") if s.strip()]

        success = apply_plugin(
            plugin_path,
            target_path,
            content_filter if content_filter else None,
            args.hooks,
            args.conflict_mode,
            args.dry_run
        )

        return 0 if success else 1

    print("请指定 --download, --check-conflicts 或 --apply")
    return 1


if __name__ == "__main__":
    sys.exit(main())
