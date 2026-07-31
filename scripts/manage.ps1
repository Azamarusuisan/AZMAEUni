[CmdletBinding()]
param(
    [Parameter(Position = 0, ValueFromRemainingArguments = $true)]
    [string[]] $ManageArguments = @()
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

function Get-WriteNoteDraftsPython {
    $candidates = New-Object System.Collections.ArrayList

    if (-not [string]::IsNullOrWhiteSpace($env:WRITE_NOTE_DRAFTS_PYTHON)) {
        [void] $candidates.Add([pscustomobject]@{
            Command = $env:WRITE_NOTE_DRAFTS_PYTHON
            Prefix = @()
        })
    }

    foreach ($version in @("3.14", "3.13", "3.12", "3.11", "3.10")) {
        [void] $candidates.Add([pscustomobject]@{
            Command = "py"
            Prefix = @("-$version")
        })
    }

    foreach ($name in @("python3", "python")) {
        [void] $candidates.Add([pscustomobject]@{
            Command = $name
            Prefix = @()
        })
    }

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.Command -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -eq $command) {
            continue
        }

        $executable = $command.Source
        if ([string]::IsNullOrWhiteSpace($executable)) {
            $executable = $command.Path
        }
        if ([string]::IsNullOrWhiteSpace($executable)) {
            continue
        }

        # Microsoft Store aliases can open a Store window instead of Python.
        if ($executable -match "\\WindowsApps\\python(?:3)?\.exe$") {
            continue
        }

        $probeArguments = @()
        $probeArguments += @($candidate.Prefix)
        $probeArguments += @(
            "-c",
            "import sys; print('.'.join(map(str, sys.version_info[:3])) + '|' + sys.executable); raise SystemExit(0 if sys.version_info >= (3, 10) else 3)"
        )

        $probe = & $executable @probeArguments 2>$null
        if ($LASTEXITCODE -ne 0 -or $null -eq $probe) {
            continue
        }

        $parts = ([string] ($probe | Select-Object -First 1)).Trim() -split "\|", 2
        if ($parts.Count -ne 2) {
            continue
        }

        $displayExecutable = $executable
        if ($displayExecutable -match "\s") {
            $displayExecutable = '"' + $displayExecutable + '"'
        }
        $invocationParts = @($displayExecutable) + @($candidate.Prefix)

        return [pscustomobject]@{
            executable = $executable
            prefix = @($candidate.Prefix)
            version = $parts[0]
            resolved_executable = $parts[1]
            invocation = ($invocationParts -join " ")
        }
    }

    return $null
}

$runtime = Get-WriteNoteDraftsPython
if ($null -eq $runtime) {
    [Console]::Error.WriteLine(
        "error: Python 3.10以上が見つかりません。winget install --id Python.Python.3.14 -e を実行し、新しいPowerShellを開いてください。"
    )
    exit 2
}

if ($ManageArguments.Count -eq 1 -and $ManageArguments[0] -eq "--print-runtime") {
    $runtime | ConvertTo-Json -Depth 4
    exit 0
}

$pythonArguments = @()
$pythonArguments += @($runtime.prefix)
$pythonArguments += (Join-Path $PSScriptRoot "manage.py")
$pythonArguments += @($ManageArguments)

& $runtime.executable @pythonArguments
exit $LASTEXITCODE
