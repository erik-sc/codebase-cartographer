<#
.SYNOPSIS
  Installs codebase-cartographer skills and agents for Claude Code.

.DESCRIPTION
  Two modes:
    -Scope user     (default) copies skills/ and agents/ into ~/.claude so every project gets them.
    -Scope project  copies them into <Target>/.claude and merges templates/settings.project.json
                    into <Target>/.claude/settings.json so the read-only allow/deny rules travel with the repo.

  Nothing here touches your existing settings keys except "permissions.allow" / "permissions.deny",
  which are unioned (never replaced). Re-running is safe.

.EXAMPLE
  .\install.ps1
  .\install.ps1 -Scope project -Target C:\code\my-app
#>
[CmdletBinding()]
param(
  [ValidateSet("user", "project")] [string] $Scope = "user",
  [string] $Target = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$src = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Scope -eq "user") {
  $dest = Join-Path $HOME ".claude"
} else {
  $dest = Join-Path $Target ".claude"
}

New-Item -ItemType Directory -Force (Join-Path $dest "skills") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $dest "agents") | Out-Null

Get-ChildItem (Join-Path $src "skills") -Directory | ForEach-Object {
  $to = Join-Path $dest "skills\$($_.Name)"
  if (Test-Path $to) { Remove-Item -Recurse -Force $to }
  Copy-Item -Recurse $_.FullName $to
  Write-Host "skill   -> $to"
}
Get-ChildItem (Join-Path $src "agents") -File | ForEach-Object {
  Copy-Item -Force $_.FullName (Join-Path $dest "agents")
  Write-Host "agent   -> $(Join-Path $dest "agents\$($_.Name)")"
}

if ($Scope -eq "project") {
  $settingsPath = Join-Path $dest "settings.json"
  $template = Get-Content (Join-Path $src "templates\settings.project.json") -Raw | ConvertFrom-Json
  if (Test-Path $settingsPath) {
    $existing = Get-Content $settingsPath -Raw | ConvertFrom-Json
  } else {
    $existing = [pscustomobject]@{}
  }
  if (-not $existing.PSObject.Properties["permissions"]) {
    $existing | Add-Member -NotePropertyName permissions -NotePropertyValue ([pscustomobject]@{})
  }
  foreach ($key in @("allow", "deny")) {
    $cur = @()
    if ($existing.permissions.PSObject.Properties[$key]) { $cur = @($existing.permissions.$key) }
    $merged = @($cur + @($template.permissions.$key) | Select-Object -Unique)
    if ($existing.permissions.PSObject.Properties[$key]) {
      $existing.permissions.$key = $merged
    } else {
      $existing.permissions | Add-Member -NotePropertyName $key -NotePropertyValue $merged
    }
  }
  $existing | ConvertTo-Json -Depth 10 | Out-File -Encoding utf8 $settingsPath
  Write-Host "settings-> $settingsPath (permissions merged)"

  $claudeMd = Join-Path $Target "CLAUDE.md"
  $snippet = Get-Content (Join-Path $src "templates\CLAUDE.md.snippet") -Raw
  if (-not (Test-Path $claudeMd) -or -not (Select-String -Path $claudeMd -Pattern "codebase-knowledge" -Quiet)) {
    Add-Content -Path $claudeMd -Value "`n$snippet" -Encoding utf8
    Write-Host "CLAUDE.md-> appended knowledge-base import"
  }
}

Write-Host ""
Write-Host "Done. In Claude Code run:  /learn-codebase   (then /ask-codebase, /trace-flow, /quiz-me)"
if ($Scope -eq "project") {
  Write-Host "Accept the workspace-trust dialog once so the allow rules apply."
}
