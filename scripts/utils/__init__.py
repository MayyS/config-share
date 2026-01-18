"""
config-share 工具模块
"""

from .file_utils import (
    copy_with_conflict,
    detect_conflicts,
    safe_delete,
    ensure_dirs_exist,
    read_agents,
    read_commands,
    parse_frontmatter,
    merge_hooks,
    load_json,
    save_json,
    get_claude_path,
    get_share_dir,
    expand_path,
    list_directory,
    is_subdirectory
)

from .config_utils import (
    read_share_plugins_json,
    write_share_plugins_json,
    create_share_plugins_json,
    validate_share_plugins_json,
    validate_version,
    increment_version,
    compare_versions,
    merge_configs,
    update_apply_record,
    calculate_file_hash,
    count_files,
    get_plugin_path,
    list_installed_plugins,
    find_plugin_by_name
)

from .git_utils import (
    init_repo,
    clone_repo,
    check_repo_exists,
    create_repo,
    add_commit,
    push_repo,
    create_tag,
    push_tags,
    get_remote_version,
    inject_token_to_url,
    get_current_branch,
    fetch,
    pull,
    add_remote,
    get_remotes
)

__all__ = [
    # file_utils
    "copy_with_conflict",
    "detect_conflicts",
    "safe_delete",
    "ensure_dirs_exist",
    "read_agents",
    "read_commands",
    "parse_frontmatter",
    "merge_hooks",
    "load_json",
    "save_json",
    "get_claude_path",
    "get_share_dir",
    "expand_path",
    "list_directory",
    "is_subdirectory",
    # config_utils
    "read_share_plugins_json",
    "write_share_plugins_json",
    "create_share_plugins_json",
    "validate_share_plugins_json",
    "validate_version",
    "increment_version",
    "compare_versions",
    "merge_configs",
    "update_apply_record",
    "calculate_file_hash",
    "count_files",
    "get_plugin_path",
    "list_installed_plugins",
    "find_plugin_by_name",
    # git_utils
    "init_repo",
    "clone_repo",
    "check_repo_exists",
    "create_repo",
    "add_commit",
    "push_repo",
    "create_tag",
    "push_tags",
    "get_remote_version",
    "inject_token_to_url",
    "get_current_branch",
    "fetch",
    "pull",
    "add_remote",
    "get_remotes"
]
