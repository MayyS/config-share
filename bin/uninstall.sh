#!/bin/bash

# Configuration
DEFAULT_ROOT="$HOME"
SKILL_NAME="config-share"

# Prompt for directory
echo "配置分享插件skills 卸载程序 (Config Share Skill Uninstaller - Linux/macOS)"
read -p "请输入安装时使用的项目目录 [默认: $DEFAULT_ROOT]: " USER_ROOT
INSTALL_ROOT="${USER_ROOT:-$DEFAULT_ROOT}"
INSTALL_ROOT="${INSTALL_ROOT%/}"
TARGET_DIR="$INSTALL_ROOT/.claude/skills/$SKILL_NAME"

if [ ! -d "$TARGET_DIR" ]; then
    echo "错误: 安装目录 '$TARGET_DIR' 不存在。"
    exit 1
fi

echo "这将永久删除: $TARGET_DIR"
read -p "您确定吗？(y/N): " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    echo "卸载已中止。"
    exit 0
fi

rm -rf "$TARGET_DIR"
echo "卸载完成。"
