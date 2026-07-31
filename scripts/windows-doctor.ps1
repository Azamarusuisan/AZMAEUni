[CmdletBinding()]
param(
    [ValidateSet("codex", "claude", "hermes")]
    [string] $Agent = "codex",

    [ValidateSet("note", "brain")]
    [string] $Target = "note",

    [string] $Workspace = (Join-Path $env:USERPROFILE ".config\write-note-drafts")
)

Set-StrictMode -Version 2.0
$ErrorActionPreference = "Stop"

$utf8 = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8
$OutputEncoding = $utf8

$checks = New-Object System.Collections.ArrayList

function Add-DoctorCheck {
    param(
        [string] $Name,
        [ValidateSet("pass", "warning", "blocked", "pending")]
        [string] $Status,
        [string] $Detail,
        [string] $Fix = ""
    )

    [void] $checks.Add([pscustomobject]@{
        name = $Name
        status = $Status
        detail = $Detail
        fix = $Fix
    })
}

function Find-ChromeExecutable {
    $candidates = New-Object System.Collections.ArrayList

    if (-not [string]::IsNullOrWhiteSpace($env:WRITE_NOTE_DRAFTS_CHROME)) {
        [void] $candidates.Add($env:WRITE_NOTE_DRAFTS_CHROME)
    }

    foreach ($root in @(
        $env:LOCALAPPDATA,
        $env:ProgramFiles,
        ${env:ProgramFiles(x86)}
    ) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }) {
        [void] $candidates.Add(
            (Join-Path $root "Google\Chrome\Application\chrome.exe")
        )
    }

    foreach ($registryPath in @(
        "HKCU:\Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        "HKLM:\Software\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe",
        "HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
    )) {
        try {
            $value = (Get-ItemProperty -Path $registryPath -ErrorAction Stop)."(default)"
            if (-not [string]::IsNullOrWhiteSpace($value)) {
                [void] $candidates.Add($value)
            }
        } catch {
            # The key is optional.
        }
    }

    $command = Get-Command "chrome.exe" -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -ne $command -and -not [string]::IsNullOrWhiteSpace($command.Source)) {
        [void] $candidates.Add($command.Source)
    }

    foreach ($candidate in $candidates | Select-Object -Unique) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [string] $candidate
        }
    }
    return $null
}

if ($env:OS -ne "Windows_NT") {
    Add-DoctorCheck "platform" "blocked" "Windowsネイティブ環境ではありません。" `
        "WSL2ではこのスクリプトではなくLinux手順を使い、リポジトリとワークスペースをWSL側へ置いてください。"
} else {
    Add-DoctorCheck "platform" "pass" "Windowsネイティブ環境を確認しました。"
}

$powerShellVersion = $PSVersionTable.PSVersion
if ($powerShellVersion -lt [version] "5.1") {
    Add-DoctorCheck "powershell" "blocked" "PowerShell $powerShellVersion は未対応です。" `
        "Windows PowerShell 5.1以上、またはPowerShell 7を使用してください。"
} else {
    Add-DoctorCheck "powershell" "pass" "PowerShell $powerShellVersion / $($PSVersionTable.PSEdition)"
}

if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") {
    Add-DoctorCheck "architecture" "warning" "Windows on ARM64です。ローカル処理は利用できますが、AgentとChrome connectorは条件付きです。" `
        "この端末でAgent runtime Doctorとファイルuploadを実行してからCMS操作へ進んでください。"
} elseif ($env:PROCESSOR_ARCHITECTURE -eq "x86") {
    Add-DoctorCheck "architecture" "blocked" "32-bit Windows processは対応対象外です。" `
        "64-bit Windowsと64-bit Pythonを使用してください。"
} else {
    Add-DoctorCheck "architecture" "pass" $env:PROCESSOR_ARCHITECTURE
}

$windowsInfo = [ordered]@{
    product_name = "Windows"
    display_version = "unknown"
    build = [Environment]::OSVersion.Version.Build
    architecture = $env:PROCESSOR_ARCHITECTURE
}
try {
    $currentVersion = Get-ItemProperty `
        -Path "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion" `
        -ErrorAction Stop
    if ($currentVersion.PSObject.Properties.Name -contains "ProductName" -and
        -not [string]::IsNullOrWhiteSpace($currentVersion.ProductName)) {
        $windowsInfo.product_name = [string] $currentVersion.ProductName
    }
    if ($currentVersion.PSObject.Properties.Name -contains "DisplayVersion" -and
        -not [string]::IsNullOrWhiteSpace($currentVersion.DisplayVersion)) {
        $windowsInfo.display_version = [string] $currentVersion.DisplayVersion
    }
    if ($currentVersion.PSObject.Properties.Name -contains "CurrentBuildNumber" -and
        -not [string]::IsNullOrWhiteSpace($currentVersion.CurrentBuildNumber)) {
        $windowsInfo.build = [int] $currentVersion.CurrentBuildNumber
    }
} catch {
    # Environment.OSVersion remains available as a fallback.
}

if ($windowsInfo.product_name -match "Server") {
    Add-DoctorCheck "windows_version" "warning" `
        "$($windowsInfo.product_name) build $($windowsInfo.build)です。CIとローカル処理には使えますが、購入者向けCMS操作の標準環境ではありません。" `
        "実運用にはGUI付きWindows 11を使用し、Chrome connectorを実機で確認してください。"
} elseif ($windowsInfo.build -ge 22000) {
    Add-DoctorCheck "windows_version" "pass" `
        "Windows 11相当のbuild $($windowsInfo.build)を確認しました。"
} elseif ($windowsInfo.build -ge 17763) {
    Add-DoctorCheck "windows_version" "warning" `
        "Windows 10 build $($windowsInfo.build)です。Skillは動作対象ですが、Codex公式ではbest effortです。" `
        "可能ならWindows 11へ更新し、少なくともWindows Updateを最新にしてください。"
} else {
    Add-DoctorCheck "windows_version" "blocked" `
        "Windows build $($windowsInfo.build)は古く、必要なConPTYを利用できない可能性があります。" `
        "Windows 11、または完全更新済みのWindows 10 build 17763以降へ更新してください。"
}

$runtime = $null
try {
    $runtimeOutput = & (Join-Path $PSScriptRoot "manage.ps1") --print-runtime 2>&1
    if ($LASTEXITCODE -eq 0) {
        $runtime = ($runtimeOutput -join "`n") | ConvertFrom-Json
        Add-DoctorCheck "python" "pass" `
            "Python $($runtime.version) ($($runtime.resolved_executable))"
    } else {
        Add-DoctorCheck "python" "blocked" ($runtimeOutput -join " ") `
            "winget install --id Python.Python.3.14 -e を実行し、新しいPowerShellを開いてください。"
    }
} catch {
    Add-DoctorCheck "python" "blocked" $_.Exception.Message `
        "winget install --id Python.Python.3.14 -e を実行し、新しいPowerShellを開いてください。"
}

$git = Get-Command "git.exe" -CommandType Application -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($null -eq $git) {
    Add-DoctorCheck "git" "warning" "GitがPATHに見つかりません。記事作成はできますが更新できません。" `
        "winget install --id Git.Git -e を実行し、新しいPowerShellを開いてください。"
} else {
    Add-DoctorCheck "git" "pass" $git.Source
}

$chrome = Find-ChromeExecutable
if ($null -eq $chrome) {
    Add-DoctorCheck "chrome" "blocked" "Google Chromeが見つかりません。WindowsではSafari経路を使えません。" `
        "winget install --id Google.Chrome -e を実行し、Chromeへ手動ログインしてください。"
} else {
    Add-DoctorCheck "chrome" "pass" $chrome
}

try {
    $longPaths = (Get-ItemProperty `
        -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
        -Name "LongPathsEnabled" `
        -ErrorAction Stop).LongPathsEnabled
    if ([int] $longPaths -eq 1) {
        Add-DoctorCheck "long_paths" "pass" "Windows long pathsが有効です。"
    } else {
        Add-DoctorCheck "long_paths" "warning" "Windows long pathsが無効です。深いフォルダで失敗する場合があります。" `
            "SkillはC:\Users\<name>\.agents\skills直下、ワークスペースはC:\Users\<name>\.config直下に置いてください。"
    }
} catch {
    Add-DoctorCheck "long_paths" "warning" "Windows long paths設定を読み取れませんでした。" `
        "パスを短く保ち、同じエラーが続く場合は管理者へ確認してください。"
}

$workspaceFullPath = [IO.Path]::GetFullPath($Workspace)
if ($workspaceFullPath.StartsWith("\\")) {
    Add-DoctorCheck "workspace_location" "warning" "workspaceがUNC/network pathです。接続切断やfile lockの影響を受けます。" `
        "ローカルの$env:USERPROFILE\.config\write-note-draftsを使用してください。"
} elseif ($workspaceFullPath.Length -gt 180) {
    Add-DoctorCheck "workspace_location" "warning" "workspace pathが長く、生成ファイルがMAX_PATHへ近づく可能性があります。" `
        "ローカルの$env:USERPROFILE\.config\write-note-draftsへ短くしてください。"
} else {
    Add-DoctorCheck "workspace_location" "pass" $workspaceFullPath
}
$oneDriveRoots = @(
    $env:OneDrive,
    $env:OneDriveConsumer,
    $env:OneDriveCommercial
) | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
$insideOneDrive = $false
foreach ($oneDriveRoot in $oneDriveRoots) {
    $rootFullPath = [IO.Path]::GetFullPath($oneDriveRoot).TrimEnd("\") + "\"
    if ($workspaceFullPath.StartsWith($rootFullPath, [StringComparison]::OrdinalIgnoreCase)) {
        $insideOneDrive = $true
        break
    }
}
if ($insideOneDrive) {
    Add-DoctorCheck "onedrive" "warning" "ワークスペースがOneDrive配下です。同期競合や一時ロックの原因になります。" `
        "既定の$env:USERPROFILE\.config\write-note-draftsへ移してください。"
} else {
    Add-DoctorCheck "onedrive" "pass" "ワークスペースは既知のOneDriveルート外です。"
}

$pythonDoctor = $null
if ($null -ne $runtime) {
    try {
        $doctorOutput = & (Join-Path $PSScriptRoot "manage.ps1") `
            doctor --browser chrome --agent $Agent --workspace $workspaceFullPath 2>&1
        if ($LASTEXITCODE -eq 0) {
            $pythonDoctor = ($doctorOutput -join "`n") | ConvertFrom-Json
            if (@($pythonDoctor.blocking_checks).Count -eq 0) {
                Add-DoctorCheck "workspace" "pass" `
                    $pythonDoctor.local_checks.workspace.detail
            } else {
                Add-DoctorCheck "workspace" "blocked" `
                    ("blocking_checks: " + (@($pythonDoctor.blocking_checks) -join ", ")) `
                    "表示されたパス・Python・platformの問題を直してから再実行してください。"
            }
        } else {
            Add-DoctorCheck "workspace" "blocked" ($doctorOutput -join " ") `
                "ワークスペースには絶対パスを指定し、Skill checkoutの外へ置いてください。"
        }
    } catch {
        Add-DoctorCheck "workspace" "blocked" $_.Exception.Message `
            "ワークスペースには絶対パスを指定し、Skill checkoutの外へ置いてください。"
    }
}

$runtimeNames = @()
if ($null -ne $pythonDoctor) {
    $runtimeNames = @($pythonDoctor.runtime_checks.PSObject.Properties.Name | Sort-Object)
}
Add-DoctorCheck "agent_runtime" "pending" `
    ("現在のエージェント内で確認する項目: " + ($runtimeNames -join ", ")) `
    "新しいエージェント会話でDoctorを実行し、Web・画像生成・Chrome接続を実際に呼び出してください。"

$blockedCount = @($checks | Where-Object { $_.status -eq "blocked" }).Count
$warningCount = @($checks | Where-Object { $_.status -eq "warning" }).Count
$status = "local_pass"
if ($blockedCount -gt 0) {
    $status = "blocked"
} elseif ($warningCount -gt 0) {
    $status = "warning"
}
$nextStep = "ローカル診断は完了です。エージェント会話内のruntime checkへ進んでください。"
if ($blockedCount -gt 0) {
    $nextStep = "blockedのfixを上から順に実行し、このDoctorを再実行してください。"
}

$result = [ordered]@{
    schema_version = 1
    status = $status
    supported_mode = "windows-native-chrome"
    agent = $Agent
    target = $Target
    workspace = $workspaceFullPath
    windows = $windowsInfo
    checks = @($checks)
    blocking_count = $blockedCount
    warning_count = $warningCount
    next_step = $nextStep
}

$result | ConvertTo-Json -Depth 8
if ($blockedCount -gt 0) {
    exit 2
}
exit 0
