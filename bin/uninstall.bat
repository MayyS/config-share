@echo off
setlocal

set "DEFAULT_ROOT=%USERPROFILE%"
set "SKILL_NAME=config-share"

echo 配置分享插件skills 卸载程序 (Config Share Skill Uninstaller - Windows CMD)
set /p "USER_ROOT=请输入安装时使用的项目目录 [默认: %DEFAULT_ROOT%]: "
if "%USER_ROOT%"=="" set "USER_ROOT=%DEFAULT_ROOT%"
if "%USER_ROOT:~-1%"=="\" set "USER_ROOT=%USER_ROOT:~0,-1%"
if "%USER_ROOT:~-1%"=="/" set "USER_ROOT=%USER_ROOT:~0,-1%"

set "TARGET_DIR=%USER_ROOT%\.claude\skills\%SKILL_NAME%"

if not exist "%TARGET_DIR%" (
    echo 错误: 安装目录 "%TARGET_DIR%" 不存在。
    pause
    exit /b 1
)

echo 这将永久删除: "%TARGET_DIR%"
set /p "CONFIRM=您确定吗？(y/N): "
if /i not "%CONFIRM%"=="y" (
    echo 卸载已中止。
    exit /b 0
)

rmdir /S /Q "%TARGET_DIR%"
echo 卸载完成。
pause
