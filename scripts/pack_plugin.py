#!/usr/bin/env python3
"""
打包插件脚本
从 Claude 配置目录打包 commands/agents/hooks/mcp 为插件
"""
import argparse
import shutil
import sys
from pathlib import Path

# 添加 utils 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "utils"))

from file_utils import (
    get_claude_path, get_share_dir, expand_path,
    copy_with_conflict, read_agents, read_commands, list_directory,
    load_json, save_json, ensure_dirs_exist
)
from config_utils import (
    create_share_plugins_json, write_share_plugins_json,
    count_files, calculate_file_hash
)
from sanitize_utils import (
    detect_sensitive_fields, sanitize_json, generate_env_example,
    count_placeholders
)


def list_packable_content(source_path: Path) -> dict:
    """
    列出可打包的内容

    Args:
        source_path: 源路径

    Returns:
        可打包内容的字典
    """
    content = {
        "commands": [],
        "agents": [],
        "hooks": None,
        "mcp": []
    }

    # Commands
    commands_dir = source_path / "commands"
    if commands_dir.exists():
        content["commands"] = [f.stem for f in list_directory(commands_dir, "*.md")]

    # Agents
    agents_dir = source_path / "agents"
    if agents_dir.exists():
        content["agents"] = [f.stem for f in list_directory(agents_dir, "*.md")]

    # Hooks
    hooks_file = source_path / "hooks.json"
    if hooks_file.exists():
        content["hooks"] = str(hooks_file)

    # MCP
    mcp_file = source_path / "mcp.json"
    if mcp_file.exists():
        content["mcp"] = ["mcp.json"]

    return content


def parse_content_list(content_list: str, available: list) -> list:
    """
    解析内容列表

    Args:
        content_list: 内容列表字符串（"all" 或逗号分隔）
        available: 可用的内容列表

    Returns:
        要包含的内容列表
    """
    if not content_list:
        return []

    if content_list.lower() == "all":
        return available

    return [item.strip() for item in content_list.split(",") if item.strip()]


def pack_commands(commands_list: list, source_path: Path, output_path: Path,
                 exclude_list: list = None, dry_run: bool = False) -> int:
    """
    打包 commands

    Args:
        commands_list: 要打包的 commands 列表
        source_path: 源路径
        output_path: 输出路径
        exclude_list: 要排除的列表
        dry_run: 试运行

    Returns:
        打包的文件数量
    """
    if not commands_list:
        return 0

    count = 0
    commands_dir = source_path / "commands"
    output_commands_dir = output_path / "commands"
    exclude_set = set(exclude_list or [])

    if dry_run:
        print(f"[DRY RUN] 会创建目录: {output_commands_dir}")

    for cmd_name in commands_list:
        if cmd_name in exclude_set:
            continue

        src_file = commands_dir / f"{cmd_name}.md"
        if not src_file.exists():
            print(f"警告: command 文件不存在: {src_file}")
            continue

        dst_file = output_commands_dir / f"{cmd_name}.md"

        if dry_run:
            print(f"[DRY RUN] 会复制: {src_file} -> {dst_file}")
        else:
            success, msg = copy_with_conflict(src_file, dst_file, mode="overwrite")
            if success:
                count += 1
                print(f"  {msg}")
            else:
                print(f"  {msg}")

    return count


def pack_agents(agents_list: list, source_path: Path, output_path: Path,
               exclude_list: list = None, dry_run: bool = False) -> int:
    """
    打包 agents

    Args:
        agents_list: 要打包的 agents 列表
        source_path: 源路径
        output_path: 输出路径
        exclude_list: 要排除的列表
        dry_run: 试运行

    Returns:
        打包的文件数量
    """
    if not agents_list:
        return 0

    count = 0
    agents_dir = source_path / "agents"
    output_agents_dir = output_path / "agents"
    exclude_set = set(exclude_list or [])

    if dry_run:
        print(f"[DRY RUN] 会创建目录: {output_agents_dir}")

    for agent_name in agents_list:
        if agent_name in exclude_set:
            continue

        src_file = agents_dir / f"{agent_name}.md"
        if not src_file.exists():
            print(f"警告: agent 文件不存在: {src_file}")
            continue

        dst_file = output_agents_dir / f"{agent_name}.md"

        if dry_run:
            print(f"[DRY RUN] 会复制: {src_file} -> {dst_file}")
        else:
            success, msg = copy_with_conflict(src_file, dst_file, mode="overwrite")
            if success:
                count += 1
                print(f"  {msg}")
            else:
                print(f"  {msg}")

    return count


def pack_hooks(include: bool, source_path: Path, output_path: Path,
              skip_sanitize: bool = False, dry_run: bool = False) -> tuple[bool, dict]:
    """
    打包 hooks

    Args:
        include: 是否包含
        source_path: 源路径
        output_path: 输出路径
        skip_sanitize: 是否跳过脱敏
        dry_run: 试运行

    Returns:
        (是否成功, 环境变量字典)
    """
    if not include:
        return False, {}

    src_file = source_path / "hooks.json"
    dst_file = output_path / "hooks.json"

    if not src_file.exists():
        print(f"警告: hooks.json 不存在: {src_file}")
        return False, {}

    # 读取 JSON 进行脱敏处理
    hooks_data = load_json(src_file)

    if hooks_data:
        env_vars = {}
        if not skip_sanitize:
            # 检测敏感字段
            env_vars = detect_sensitive_fields(hooks_data)
            if env_vars:
                print(f"  检测到 {len(env_vars)} 个敏感字段，正在脱敏...")
                hooks_data = sanitize_json(hooks_data, env_vars)
    else:
        env_vars = {}

    if dry_run:
        if env_vars:
            print(f"[DRY RUN] 会脱敏并写入: {src_file} -> {dst_file}")
        else:
            print(f"[DRY RUN] 会复制: {src_file} -> {dst_file}")
        return True, env_vars

    # 写入处理后的 JSON
    if hooks_data:
        if save_json(dst_file, hooks_data):
            print(f"  成功处理: {dst_file}")
            placeholder_count = count_placeholders(hooks_data)
            if placeholder_count > 0:
                print(f"    已替换 {placeholder_count} 个敏感值为环境变量占位符")
            return True, env_vars
        else:
            print(f"  写入失败: {dst_file}")
            return False, env_vars
    else:
        success, msg = copy_with_conflict(src_file, dst_file, mode="overwrite")
        if success:
            print(f"  {msg}")
            return True, {}
        else:
            print(f"  {msg}")
            return False, {}


def pack_mcp(include: bool, source_path: Path, output_path: Path,
            skip_sanitize: bool = False, dry_run: bool = False) -> tuple[bool, dict]:
    """
    打包 mcp

    Args:
        include: 是否包含
        source_path: 源路径
        output_path: 输出路径
        skip_sanitize: 是否跳过脱敏
        dry_run: 试运行

    Returns:
        (是否成功, 环境变量字典)
    """
    if not include:
        return False, {}

    src_file = source_path / "mcp.json"
    dst_file = output_path / "mcp.json"

    if not src_file.exists():
        print(f"警告: mcp.json 不存在: {src_file}")
        return False, {}

    # 读取 JSON 进行脱敏处理
    mcp_data = load_json(src_file)

    if mcp_data:
        env_vars = {}
        if not skip_sanitize:
            # 检测敏感字段
            env_vars = detect_sensitive_fields(mcp_data)
            if env_vars:
                print(f"  检测到 {len(env_vars)} 个敏感字段，正在脱敏...")
                mcp_data = sanitize_json(mcp_data, env_vars)
    else:
        env_vars = {}

    if dry_run:
        if env_vars:
            print(f"[DRY RUN] 会脱敏并写入: {src_file} -> {dst_file}")
        else:
            print(f"[DRY RUN] 会复制: {src_file} -> {dst_file}")
        return True, env_vars

    # 写入处理后的 JSON
    if mcp_data:
        if save_json(dst_file, mcp_data):
            print(f"  成功处理: {dst_file}")
            placeholder_count = count_placeholders(mcp_data)
            if placeholder_count > 0:
                print(f"    已替换 {placeholder_count} 个敏感值为环境变量占位符")
            return True, env_vars
        else:
            print(f"  写入失败: {dst_file}")
            return False, env_vars
    else:
        success, msg = copy_with_conflict(src_file, dst_file, mode="overwrite")
        if success:
            print(f"  {msg}")
            return True, {}
        else:
            print(f"  {msg}")
            return False, {}


def main():
    parser = argparse.ArgumentParser(description="打包 Claude Code 配置为插件")
    parser.add_argument("--source", type=str, default="~/.claude/",
                        help="源路径，默认 ~/.claude/")
    parser.add_argument("--output", type=str, default="./claude_share/",
                        help="输出路径，默认 ./claude_share/")
    parser.add_argument("--name", type=str, required=True,
                        help="插件名称")
    parser.add_argument("--version", type=str, default="1.0.0",
                        help="版本号，默认 1.0.0")
    parser.add_argument("--commands", type=str, default="",
                        help="包含的 commands (all 或逗号分隔的文件名)")
    parser.add_argument("--agents", type=str, default="",
                        help="包含的 agents (all 或逗号分隔的文件名)")
    parser.add_argument("--hooks", action="store_true",
                        help="是否包含 hooks")
    parser.add_argument("--mcp", action="store_true",
                        help="是否包含 mcp")
    parser.add_argument("--exclude", type=str, default="{}",
                        help="排除的文件 JSON 格式")
    parser.add_argument("--description", type=str, default="",
                        help="插件描述")
    parser.add_argument("--author", type=str, default="",
                        help="作者")
    parser.add_argument("--license", type=str, default="MIT",
                        help="许可证")
    parser.add_argument("--list", action="store_true",
                        help="列出可打包内容")
    parser.add_argument("--dry-run", action="store_true",
                        help="试运行")
    parser.add_argument("--skip-sanitize", action="store_true",
                        help="跳过敏感信息脱敏（保留原始值）")

    args = parser.parse_args()

    # 解析路径
    source_path = expand_path(args.source)
    output_path = Path(args.output)

    if not source_path.exists():
        print(f"错误: 源路径不存在: {source_path}")
        return 1

    # 列出可打包内容
    if args.list:
        content = list_packable_content(source_path)
        print("可打包的内容:")
        print(f"  Commands: {', '.join(content['commands']) or '无'}")
        print(f"  Agents: {', '.join(content['agents']) or '无'}")
        print(f"  Hooks: {'hooks.json' if content['hooks'] else '无'}")
        print(f"  MCP: {', '.join(content['mcp']) or '无'}")
        return 0

    # 解析排除列表
    try:
        import json
        exclude = json.loads(args.exclude)
    except json.JSONDecodeError:
        print("错误: --exclude 参数必须是有效的 JSON")
        return 1

    # 插件输出目录
    plugin_dir = output_path / args.name

    # 检查插件是否已存在
    if plugin_dir.exists():
        if not args.dry_run:
            response = input(f"插件目录已存在: {plugin_dir}，是否覆盖？(y/N): ")
            if response.lower() != 'y':
                print("已取消")
                return 1
            shutil.rmtree(plugin_dir)
    elif not args.dry_run:
        ensure_dirs_exist([plugin_dir])

    # 打包内容
    print(f"打包插件: {args.name}")
    print(f"  源路径: {source_path}")
    print(f"  输出路径: {plugin_dir}")
    print(f"  版本: {args.version}")
    print()

    file_count = 0

    # Commands
    available_commands = list_directory(source_path / "commands", "*.md")
    available_commands = [f.stem for f in available_commands]
    commands_list = parse_content_list(args.commands, available_commands)
    if commands_list:
        print("打包 Commands:")
        file_count += pack_commands(
            commands_list,
            source_path,
            plugin_dir,
            exclude.get("commands", []),
            args.dry_run
        )

    # Agents
    available_agents = list_directory(source_path / "agents", "*.md")
    available_agents = [f.stem for f in available_agents]
    agents_list = parse_content_list(args.agents, available_agents)
    if agents_list:
        print("打包 Agents:")
        file_count += pack_agents(
            agents_list,
            source_path,
            plugin_dir,
            exclude.get("agents", []),
            args.dry_run
        )

    # Hooks
    all_env_vars = {}
    if args.hooks:
        print("打包 Hooks:")
        success, hooks_envs = pack_hooks(
            True, source_path, plugin_dir, args.skip_sanitize, args.dry_run
        )
        if success:
            file_count += 1
            all_env_vars.update(hooks_envs)

    # MCP
    if args.mcp:
        print("打包 MCP:")
        success, mcp_envs = pack_mcp(
            True, source_path, plugin_dir, args.skip_sanitize, args.dry_run
        )
        if success:
            file_count += 1
            all_env_vars.update(mcp_envs)

    # 创建 .env.example 文件（如果有敏感信息）
    if all_env_vars and not args.skip_sanitize and not args.dry_run:
        env_example = generate_env_example(all_env_vars)
        env_file = plugin_dir / ".env.example"
        env_file.write_text(env_example)
        print()
        print(f"创建: {env_file} (包含 {len(all_env_vars)} 个环境变量模板)")
        print("提示: 使用插件时，请复制 .env.example 为 .env 并填入真实值")

    # 创建 share_plugins.json
    print()
    if not args.dry_run:
        plugin_data = create_share_plugins_json(
            args.name,
            args.version,
            args.description,
            args.author,
            args.license
        )

        plugin_data["content"]["commands"] = commands_list if commands_list != available_commands else ["all"]
        plugin_data["content"]["agents"] = agents_list
        plugin_data["content"]["hooks"] = ["hooks.json"] if args.hooks else []
        plugin_data["content"]["mcp"] = ["mcp.json"] if args.mcp else []
        plugin_data["exclude"] = exclude
        plugin_data["metadata"]["file_count"] = file_count

        json_file = plugin_dir / "share_plugins.json"
        write_share_plugins_json(json_file, plugin_data)
        print(f"创建: {json_file}")
    else:
        print(f"[DRY RUN] 会创建: {plugin_dir / 'share_plugins.json'}")

    print()
    print(f"完成! 打包了 {file_count} 个文件")
    if args.dry_run:
        print("试运行完成，未实际修改文件")

    return 0


if __name__ == "__main__":
    sys.exit(main())
