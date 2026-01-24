# Config Share Skill Uninstaller (PowerShell)

$ErrorActionPreference = "Stop"
$DefaultRoot = $env:USERPROFILE
$SkillName = "config-share"

Write-Host "配置分享插件skills 卸载程序 (Config Share Skill Uninstaller - PowerShell)"
$UserRoot = Read-Host "请输入安装时使用的项目目录 [默认: $DefaultRoot]"
if ([string]::IsNullOrWhiteSpace($UserRoot)) {
    $UserRoot = $DefaultRoot
}
$UserRoot = $UserRoot.TrimEnd('\/')

$TargetDir = Join-Path $UserRoot ".claude\skills\$SkillName"

if (-not (Test-Path -Path $TargetDir)) {
    Write-Error "错误: 安装目录 '$TargetDir' 不存在。"
    exit
}

Write-Host "这将永久删除: $TargetDir"
$Confirm = Read-Host "您确定吗？(y/N)"
if ($Confirm -notmatch "^[Yy]$") {
    Write-Host "卸载已中止。"
    exit
}

Remove-Item -Path $TargetDir -Recurse -Force
Write-Host "卸载完成。"
