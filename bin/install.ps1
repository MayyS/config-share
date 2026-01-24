# Config Share Skill Installer (PowerShell)

$ErrorActionPreference = "Stop"
$DefaultRoot = $env:USERPROFILE
$SkillName = "config-share"
$SrcDir = Join-Path $PSScriptRoot ".."

Write-Host "配置分享插件skills (Config Share Skill Installer - PowerShell)"
$UserRoot = Read-Host "请输入安装项目目录 [默认: $DefaultRoot]"
if ([string]::IsNullOrWhiteSpace($UserRoot)) {
    $UserRoot = $DefaultRoot
}
$UserRoot = $UserRoot.TrimEnd('\/')

$TargetDir = Join-Path $UserRoot ".claude\skills\$SkillName"
Write-Host "正在安装到: $TargetDir"

if (Test-Path -Path $TargetDir) {
    $Confirm = Read-Host "目录 '$TargetDir' 已存在。是否覆盖？(y/N)"
    if ($Confirm -notmatch "^[Yy]$") {
        Write-Host "安装已中止。"
        exit
    }
    Write-Host "正在移除现有安装..."
    Remove-Item -Path $TargetDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null

Write-Host "正在复制文件..."
$FilesToCopy = @("SKILL.md", "README.md", "requirements.txt")
foreach ($File in $FilesToCopy) {
    $SrcFile = Join-Path $SrcDir $File
    if (Test-Path $SrcFile) {
        Copy-Item -Path $SrcFile -Destination $TargetDir -Force
    } else {
        Write-Warning "警告: 源文件 '$File' 未找到。"
    }
}

$ScriptsDir = Join-Path $SrcDir "scripts"
if (Test-Path $ScriptsDir) {
    Copy-Item -Path $ScriptsDir -Destination $TargetDir -Recurse -Force
}

# Cleanup __pycache__
Get-ChildItem -Path $TargetDir -Include "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force

Write-Host "安装完成！"
Write-Host "插件已安装至: $TargetDir"
