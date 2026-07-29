# Safari browser provider

## 適用条件

`.state/workspace.json.browser` が `safari` の場合だけ使用する。今回の依頼でSafariが指定されても、保存済みproviderを確認なく変更しない。Chrome失敗時の自動fallbackとして選択しない。

Safari providerはmacOS Computer Use経由で、利用者の既存Safariプロファイルとログイン済みセッションを操作する。[agent compatibility](agent-compatibility.md)で現在hostのComputer Use capabilityを選ぶ。Safari以外のOS、専用能力、または必要なmacOS権限が利用できない場合は、外部変更前に停止する。

## 実行前の能力確認

次をすべて確認する。

- 実行環境がmacOS
- Computer Useでdesktop appを観察・操作できる
- 現在hostのComputer Use plugin/MCP/toolが利用できる
- Safariを一意に選択できる
- 画面の意味的な対象を確認できる
- Safariがnoteを開ける状態

現在hostのComputer Useが未提供ならtool discoveryを行う。利用可能にならなければ、Safariを起動、クリック、入力せず、[cms-note.mdの失敗報告](cms-note.md#失敗報告)を返す。

権限不足、Screen Recording、Accessibility、アプリ選択の失敗は利用者による解決を待つ。許可を回避するためにAppleScript、shell UI操作、JavaScript injection、別browser providerを使わない。

## 接続と観察

### Codex

ChatGPTのComputer Use pluginがインストール・有効化され、現在のWork/Codex chatへ公開されている場合だけ使う。インストール済みpluginの `SKILL.md` と完全なtool documentationを読み、そこに記載された接続・観察・操作APIだけを使う。特定のscript pathやAPIを別環境へ仮定しない。Safariを実行中アプリとして一意に確認できなければ停止する。

### Claude Code

互換性のあるsemantic Computer Use MCP/Skillが現在sessionへ接続済みで、Safari、Accessibility、Screen Recordingを利用できる場合だけ使う。提供されたtool documentationを完全に読み、fresh observationから一意なsemantic targetを取得できなければ停止する。Claude CodeやClaude in ChromeだけではSafari対応とみなさない。

### Hermes Agent

`hermes computer-use status` と現在sessionの `computer_use` toolを確認し、`macos-computer-use` Skillを読む。各操作前に `computer_use(action="capture", mode="som", app="Safari")` で再観察し、fresh indexだけを次の1操作に使う。`cua-driver`、権限、またはSafari検出に失敗したら停止する。

各操作前にSafariを新しく観察し、次の情報を確認する。

- Safariが前面の対象アプリ
- 現在のURLまたは画面上のlocationがnote adapterの許可範囲
- 期待するnote画面
- 対象のrole、label、accessible name、表示テキスト
- 対象が一意

Codexではインストール済みpluginのfreshなsemantic observation、HermesではfreshなSOM capture、Claudeでは接続toolの同等semantic observationを使う。返された現在indexだけを次の1操作に利用し、過去のindexを再利用しない。

固定座標、記録済み座標、ウィンドウ位置を前提とする操作は禁止する。Computer Useが最終的にpoint入力を必要とする場合も、現在の観察で一意に特定したsemantic targetの範囲から毎回導出する。意味的に確認できない対象はクリックしない。

## セッション

- 新しいSafariプロファイルやprivate windowを作らない。
- Password、Cookie、session token、MFA codeを要求、読出し、保存しない。
- 未ログインなら利用者へSafari上での手動ログインを依頼して待機する。
- アカウント切替を操作しない。
- 現在のnote handleを観察し、note adapterへ返す。

## 操作規則

各書込みは[cms-note.md](cms-note.md)が許可したaction IDだけを実行する。対象が0件または複数件、未知画面、公開関連画面、MFA、CAPTCHA、利用規約同意、許可外locationでは停止する。

操作後は画面を再観察し、期待状態に変わったことを確認する。screenshot、画面全体の文字列、認証状態は既定で永続化しない。

Safari固有の観察差だけをこのproviderで吸収し、記事構造、handle照合、下書き保存、再読fingerprintの判定はnote adapterへ委ねる。

## 利用不可時

失敗報告には不足能力または権限、外部変更が行われていないこと、最後の安全なcheckpoint、利用者がSafariを利用可能にする手順を記載する。Chromeへ変更する場合は利用者が明示的にproviderを変更してから別runとして再開する。
