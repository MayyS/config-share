@echo off
setlocal EnableDelayedExpansion

set "DEFAULT_ROOT=%USERPROFILE%"
set "SKILL_NAME=config-share"
set "SRC_DIR=%~dp0.."

echo 配置分享插件skills (Config Share Skill Installer - Windows CMD)
set /p "USER_ROOT=请输入安装项目目录 [默认: %DEFAULT_ROOT%]: "
if "%USER_ROOT%"=="" set "USER_ROOT=%DEFAULT_ROOT%"
if "%USER_ROOT:~-1%"=="\" set "USER_ROOT=%USER_ROOT:~0,-1%"
if "%USER_ROOT:~-1%"=="/" set "USER_ROOT=%USER_ROOT:~0,-1%"

set "TARGET_DIR=%USER_ROOT%\.claude\skills\%SKILL_NAME%"

echo 正在安装到: "%TARGET_DIR%"

if exist "%TARGET_DIR%" (
    set /p "CONFIRM=目录已存在。是否覆盖？(y/N): "
    if /i not "!CONFIRM!"=="y" (
        echo 安装已中止。
        exit /b 1
    )
    echo 正在移除现有安装...
    rmdir /S /Q "%TARGET_DIR%"
)

if not exist "%TARGET_DIR%" mkdir "%TARGET_DIR%"

echo 正在复制文件...
if exist "%SRC_DIR%\SKILL.md" copy "%SRC_DIR%\SKILL.md" "%TARGET_DIR%\" >nul
if exist "%SRC_DIR%\README.md" copy "%SRC_DIR%\README.md" "%TARGET_DIR%\" >nul
if exist "%SRC_DIR%\requirements.txt" copy "%SRC_DIR%\requirements.txt" "%TARGET_DIR%\" >nul

if exist "%SRC_DIR%\scripts" (
    xcopy "%SRC_DIR%\scripts" "%TARGET_DIR%\scripts" /E /I /Y >nul
)

:: Cleanup __pycache__
for /d /r "%TARGET_DIR%" %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

echo 安装完成！
echo 插件已安装至: "%TARGET_DIR%"
pause
