# Windows support and recovery

## Support promise

Windowsでは、環境差を推測で通さない。ローカル診断で判定できる項目は
`scripts/windows-doctor.ps1`で検査し、ブラウザや画像生成のように現在の
Agentセッションでしか判定できない項目は`pending`としてAgent側のDoctorへ渡す。

| Environment | Support level | Operation mode |
|---|---|---|
| Windows 11（最新の更新を適用） | 推奨・CI対象 | ネイティブPowerShell + Google Chrome |
| Windows 10 build 17763以降（完全更新済み） | best effort | ネイティブPowerShell + Google Chrome |
| Windows 10 build 17763未満 | 非対応 | OS更新が必要 |
| Windows on ARM64 | 条件付き | ローカル処理は対応。Agent・Chrome connectorは実機Doctorで確認 |
| WSL2 | 別経路で対応 | Linux手順。checkoutとworkspaceをWSLのhome配下へ置く |
| WSL1 | 非対応 | WSL2へ更新する |
| Windows Server／GUIのない環境 | CMS操作は非対応 | ローカル記事生成まで |
| 会社管理PC | 条件付き | sandbox、拡張、実行ポリシーを管理者が許可した範囲だけ |

Codexについては、公式のWindows資料に従いWindows 11を推奨する。更新済みWindows
10はbest effortで、ConPTYを持つbuild 17763以降を下限とする。Codex `0.115`
以降はWSL1をサポートしない。

- <https://learn.chatgpt.com/docs/windows/windows-app.md>
- <https://learn.chatgpt.com/docs/windows/windows-sandbox.md>
- <https://learn.chatgpt.com/docs/windows/wsl.md>

## 最初に実行するコマンド

PowerShell 5.1またはPowerShell 7で、Skillのルートから実行する。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\windows-doctor.ps1 `
  -Agent codex -Target note
```

`-ExecutionPolicy Bypass`はこの1プロセスだけに適用され、端末全体の設定を変更しない。
会社のGroup Policyが実行を禁止する場合は回避せず、管理者へ許可を依頼する。

Doctorは次を検査する。

- Windows buildとPowerShellの版
- Python 3.10以上の実体
- GitとGoogle Chrome
- workspaceの作成・書き込み
- Windows long paths
- OneDrive配下かどうか
- Agent、対象CMS、Chromeに必要なruntime check

結果の意味:

| Status | Meaning | Next action |
|---|---|---|
| `local_pass` | ローカル環境は通過 | Agent会話内のruntime checkへ進む |
| `warning` | 続行可能だが不安定要因あり | `fix`を読み、可能なら先に解消 |
| `blocked` | CMSを触ってはいけない | `blocked`の`fix`を上から順に実行 |
| Checkの`pending` | shellから確認できない | AgentがWeb・画像・Chromeを実際に呼び出す |

## Pythonを固定しないランチャー

Windowsのコマンドは`py -3.11`のように版を固定せず、次を使う。

```powershell
.\scripts\manage.ps1 self-check
.\scripts\manage.ps1 doctor --browser chrome --agent codex `
  --workspace "$env:USERPROFILE\.config\write-note-drafts"
```

`manage.ps1`はPython 3.14、3.13、3.12、3.11、3.10の順に利用可能な実体を探す。
Microsoft Storeの見せかけの`python.exe`は使わない。特定のPythonを使う場合だけ、
実ファイルを明示する。

```powershell
$env:WRITE_NOTE_DRAFTS_PYTHON = "C:\Python312\python.exe"
.\scripts\manage.ps1 self-check
```

企業配布などでChromeが標準場所以外にある場合だけ、実ファイルを指定して再診断する。

```powershell
$env:WRITE_NOTE_DRAFTS_CHROME = "D:\Apps\Google\Chrome\Application\chrome.exe"
.\scripts\windows-doctor.ps1 -Agent codex -Target note
```

## 必要なソフト

`winget`が使える個人PCでは次で揃えられる。インストール後はPowerShellを閉じ、
新しいウィンドウを開く。

```powershell
winget install --id Git.Git -e
winget install --id GitHub.cli -e
winget install --id Python.Python.3.14 -e
winget install --id Google.Chrome -e
```

`winget`がない端末では、Microsoft Storeのエイリアスへ依存せず、各公式
インストーラを使う。会社管理PCでは無断で管理者権限を取得せず、IT管理者へ依頼する。

## Agent別のWindowsブラウザ経路

| Agent | Windows browser | Runtime check |
|---|---|---|
| Codex | ChatGPT/Codex Windows app + Chrome Plugin | `chrome_connector` |
| Claude Code | 接続済みClaude in Chrome | `claude_in_chrome` |
| Hermes | 利用者が承認したlocal Chromium CDP session | `browser_cdp` |

WindowsではSafariへfallbackしない。Chrome接続に失敗したらCMS変更前に停止し、
ローカルの`article.md`、画像、手動転記手順を残す。

CodexのChrome PluginはGoogle Chromeだけが対象で、他のChromium browserは
対応扱いにしない。ファイルuploadが必要な場合は、Chrome拡張の詳細で
**Allow access to file URLs**を有効にし、新しいチャットで再確認する。

## Native WindowsとWSL2を混ぜない

初めて使う購入者にはNative Windowsを推奨する。

### Native Windows

- checkout: `%USERPROFILE%\.agents\skills\write-note-drafts`
- workspace: `%USERPROFILE%\.config\write-note-drafts`
- command: `scripts\manage.ps1`
- browser: Windows側のGoogle Chrome

### WSL2

- checkout: `~/.agents/skills/write-note-drafts`
- workspace: `~/.config/write-note-drafts`
- command: `python3 scripts/manage.py`
- browser: AgentのWSL設定とruntime Doctorで確認

WSL2では`/mnt/c`よりLinux home配下のほうが速く、symlinkや権限の問題が少ない。
Native Windows agentで`\\wsl$`のprojectを開くより、Windows driveへcheckoutするか、
Agent自体をWSL modeへ切り替えて再起動する。

## Error map

### `python`を実行するとMicrosoft Storeが開く

`python.exe`のApp Execution Aliasであり、Python本体ではない。`manage.ps1`はこの
aliasを無視する。`winget install --id Python.Python.3.14 -e`でPythonを入れ、
新しいPowerShellを開く。

### `running scripts is disabled on this system`

この実行だけ許可する。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File .\scripts\windows-doctor.ps1
```

Group Policyで拒否される会社PCでは設定を変更せず、管理者へ依頼する。

### `Access is denied`／workspace write probeが`blocked`

OneDrive、Desktop、Documents、network drive、Controlled Folder Accessの対象を避け、
`%USERPROFILE%\.config\write-note-drafts`を使う。フォルダのACLを無断で広げない。

### 長いパスでcloneまたは画像保存に失敗する

checkoutとworkspaceを上記の短い既定パスへ置く。`windows-doctor.ps1`が
`long_paths: warning`を返す端末では、深いprojectフォルダや長いrun IDを避ける。
管理端末のregistryは自分で変更せず、必要なら管理者へ依頼する。

### 日本語ユーザー名・空白を含むパス

すべてのパスをPowerShellでダブルクォートする。`manage.ps1`とWindows CIでは、
`購入者 環境`という日本語・空白入りworkspaceで`init`、`status`、`validate`を試験対象にする。

### OneDriveでファイルが競合する

workspaceをOneDrive外へ移す。公開用の完成原稿だけをあとからOneDriveへcopyし、
`.state`や作業中のrunを同期対象にしない。

### Chrome connectorが見つからない

1. Google ChromeとAgentアプリを更新する。
2. 拡張とPluginを有効にする。
3. 同じChrome profileでside panelまたはconnectorを開く。
4. ChromeとAgentアプリを再起動する。
5. 新しいチャットでDoctorを再実行する。

Codexの場合は公式Chrome troubleshootingも参照する。
<https://learn.chatgpt.com/docs/chrome-extension.md>

### Codex sandbox error `1385`

Windows policyがsandbox userのlogonを拒否している。管理者へlogon rightsを確認し、
調査中はCodex公式の`unelevated` sandboxを一時fallbackとして使う。共有する診断は
`$env:CODEX_HOME\.sandbox\sandbox.log`（既定は
`$env:USERPROFILE\.codex\.sandbox\sandbox.log`）だけとし、`.sandbox-secrets`は送らない。

### Windows PowerShellでjunctionを作れない

管理者権限が不要なPowerShellのJunctionを使う。既存パスへ上書きしない。

```powershell
$source = "$env:USERPROFILE\.agents\skills\write-note-drafts"
$target = "$env:USERPROFILE\.claude\skills\write-note-drafts"
New-Item -ItemType Directory -Force (Split-Path $target) | Out-Null
New-Item -ItemType Junction -Path $target -Target $source
```

削除するときはlink側だけを`Remove-Item $target`で削除する。sourceを再帰削除しない。

## CI coverage and remaining boundary

GitHub Actionsの`windows-latest`で次を実行する。

- Python 3.10、3.12、3.14
- PowerShell 7とWindows PowerShell 5.1
- package validationと`self-check`
- 日本語・空白入りworkspaceの`init`、`status`、`validate`
- native Windows Doctor

CIはGoogle Chromeへの接続後のnote実画面や、各購入者の会社Policyまでは再現できない。
この部分は実行ごとのruntime Doctorで確認し、通らない場合はCMSへ触れずに手動転記へ
切り替える。
