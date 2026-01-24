#!/bin/bash

# Configuration
DEFAULT_ROOT="$HOME"
SKILL_NAME="config-share"
SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Prompt for installation directory
echo "配置分享插件skills (Config Share Skill Installer - Linux/macOS)"
read -p "请输入安装项目目录 [默认: $DEFAULT_ROOT]: " USER_ROOT
INSTALL_ROOT="${USER_ROOT:-$DEFAULT_ROOT}"
INSTALL_ROOT="${INSTALL_ROOT%/}"
TARGET_DIR="$INSTALL_ROOT/.claude/skills/$SKILL_NAME"

echo "正在安装到: $TARGET_DIR"

# Check if target exists
if [ -d "$TARGET_DIR" ]; then
    read -p "目录 '$TARGET_DIR' 已存在。是否覆盖？(y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "安装已中止。"
        exit 1
    fi
    echo "正在移除现有安装..."
    rm -rf "$TARGET_DIR"
fi

# Create target directory
mkdir -p "$TARGET_DIR"
if [ $? -ne 0 ]; then
    echo "错误: 无法创建目录 '$TARGET_DIR'。请检查权限。"
    exit 1
fi

# Copy essential files
echo "正在复制文件..."
FILES_TO_COPY=("SKILL.md" "README.md" "requirements.txt")

for file in "${FILES_TO_COPY[@]}"; do
    if [ -f "$SRC_DIR/$file" ]; then
        cp "$SRC_DIR/$file" "$TARGET_DIR/"
    else
        echo "警告: 源文件 '$file' 未找到。"
    fi
done

# Copy scripts directory
if [ -d "$SRC_DIR/scripts" ]; then
    cp -r "$SRC_DIR/scripts" "$TARGET_DIR/"
else
    echo "警告: 未找到 'scripts' 目录。"
fi

# Cleanup __pycache__ in the installed directory
find "$TARGET_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

echo "安装完成！"
echo "插件已安装至: $TARGET_DIR"
echo "您现在可以在 Claude Code 中使用 config-share 技能了。"
